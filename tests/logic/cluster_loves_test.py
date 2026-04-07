# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, timedelta

import mock
import pytest

from loveapp.logic.love import cluster_loves_by_time
from loveapp.models import Love
from testing.factories import create_employee


class MockLove:
    """A mock Love object for testing cluster_loves_by_time."""
    def __init__(self, message, timestamp, secret=False, sender_key=None, recipient_key=None):
        self.message = message
        self.timestamp = timestamp
        self.seconds_since_epoch = int(timestamp.timestamp())
        self.secret = secret
        self.sender_key = sender_key
        self.recipient_key = recipient_key
        self.emote = None  # Not used in this test, but included for completeness


@pytest.mark.usefixtures('gae_testbed')
class TestClusterLoves(unittest.TestCase):
    def setUp(self):
        self.alice = create_employee(username='alice')
        self.bob = create_employee(username='bob')
        self.carol = create_employee(username='carol')
        self.dave = create_employee(username='dave')
        
        # Base timestamp for creating love objects
        self.base_time = datetime.now()

    def test_basic_content_clustering(self):
        """Test that loves with identical content are clustered together."""        
        # Create loves with identical content but different timestamps
        loves = [
            MockLove("Great job!", self.base_time, sender_key=self.alice.key, recipient_key=self.bob.key),
            MockLove("Great job!", self.base_time + timedelta(minutes=30), sender_key=self.carol.key, recipient_key=self.dave.key),
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # Should have one cluster with both loves
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]['content'], "Great job!")
        self.assertEqual(clusters[0]['sender_count'], 2)
        self.assertEqual(clusters[0]['recipient_count'], 2)

    def test_secret_status_separation(self):
        """Test that loves are separated by secret status."""

        # Create loves with identical content but different secret status
        loves = [
            MockLove("Great job!", self.base_time, secret=False, sender_key=self.alice.key, recipient_key=self.bob.key),
            MockLove("Great job!", self.base_time + timedelta(minutes=30), secret=True, sender_key=self.carol.key, recipient_key=self.dave.key),
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # Should have two clusters, one secret and one not
        self.assertEqual(len(clusters), 2)
        # Check that we have one secret and one non-secret cluster
        secret_clusters = [c for c in clusters if c['is_secret']]
        non_secret_clusters = [c for c in clusters if not c['is_secret']]
        self.assertEqual(len(secret_clusters), 1)
        self.assertEqual(len(non_secret_clusters), 1)

    def test_temporal_clustering(self):
        """Test that loves are clustered by time window."""
        # Create loves with identical content but timestamps outside the default window
        loves = [
            MockLove("Great job!", self.base_time, sender_key=self.alice.key, recipient_key=self.bob.key),
            # This one is 2 days later, should be in a separate cluster with default window of 1 day
            MockLove("Great job!", self.base_time + timedelta(days=2), sender_key=self.carol.key, recipient_key=self.dave.key),
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # Should have two clusters due to time separation
        self.assertEqual(len(clusters), 2)
        
        # Test with custom time window that would include both
        clusters_with_larger_window = cluster_loves_by_time(loves, time_window_days=3)
        self.assertEqual(len(clusters_with_larger_window), 1)

    def test_sender_recipient_aggregation(self):
        """Test that unique senders and recipients are properly aggregated."""
        # Create loves with same content but overlapping senders and recipients
        loves = [
            # Alice loves Bob
            MockLove("Great team!", self.base_time, sender_key=self.alice.key, recipient_key=self.bob.key),
            # Alice loves Carol too
            MockLove("Great team!", self.base_time + timedelta(minutes=10), sender_key=self.alice.key, recipient_key=self.carol.key),
            # Dave also loves Bob
            MockLove("Great team!", self.base_time + timedelta(minutes=20), sender_key=self.dave.key, recipient_key=self.bob.key),
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # Should have one cluster with 2 unique senders and 2 unique recipients
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]['sender_count'], 2)  # Alice and Dave
        self.assertEqual(clusters[0]['recipient_count'], 2)  # Bob and Carol

    def test_timestamp_sorting(self):
        """Test that clusters are sorted by most recent timestamp."""
        # Create different loves with different timestamps
        loves = [
            # Older message
            MockLove("Good work!", self.base_time - timedelta(days=1), sender_key=self.alice.key, recipient_key=self.bob.key),
            # Newer message
            MockLove("Great job!", self.base_time, sender_key=self.carol.key, recipient_key=self.dave.key),
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # Should have two clusters, with the newer one first
        self.assertEqual(len(clusters), 2)
        self.assertEqual(clusters[0]['content'], "Great job!")
        self.assertEqual(clusters[1]['content'], "Good work!")

    def test_complex_clustering(self):
        """Test a complex scenario with multiple clustering criteria."""
        # Create various loves with different properties
        loves = [

            # Same content but 2 days later (separate cluster)
            MockLove("Great job!", self.base_time + timedelta(days=2), sender_key=self.alice.key, recipient_key=self.carol.key),

            # Same content but secret
            MockLove("Great job!", self.base_time + timedelta(hours=3), secret=True, sender_key=self.dave.key, recipient_key=self.alice.key),

            # Same content, same day
            MockLove("Great job!", self.base_time, sender_key=self.alice.key, recipient_key=self.bob.key),
            MockLove("Great job!", self.base_time + timedelta(hours=2), sender_key=self.carol.key, recipient_key=self.dave.key),
            
            # Different content
            MockLove("Nice presentation!", self.base_time + timedelta(hours=1), sender_key=self.bob.key, recipient_key=self.alice.key)
            
        ]
        
        clusters = cluster_loves_by_time(loves)
        
        # pretty sure this is wrong.
        # Should have 4 clusters:
        # 1. "Great job!" (non-secret, recent)
        # 2. "Great job!" (secret)
        # 3. "Nice presentation!"
        # 4. "Great job!" (non-secret, older)
        self.assertEqual(len(clusters), 4)
        
        # Verify they're in the right order (most recent first)
        self.assertEqual(clusters[0]['content'], "Great job!")
        self.assertFalse(clusters[0]['is_secret'])  # The recent non-secret one
        self.assertEqual(clusters[0]['sender_count'], 1)  # Alice 

        self.assertEqual(clusters[1]['content'], "Great job!")
        self.assertTrue(clusters[1]['is_secret'])  
        self.assertEqual(clusters[1]['sender_count'], 1)  # Dave

        self.assertEqual(clusters[2]['content'], "Great job!")  # The older one
        self.assertFalse(clusters[2]['is_secret'])
        self.assertEqual(clusters[2]['sender_count'], 2)  # Alice and Carol

        self.assertEqual(clusters[3]['content'], "Nice presentation!")
        self.assertFalse(clusters[3]['is_secret'])
        self.assertEqual(clusters[3]['sender_count'], 1)  # Bob   




