# -*- coding: utf-8 -*-
from datetime import datetime
from time import mktime

import mock
import pytest
from google.appengine.ext import ndb

from loveapp.models import Love
from testing.factories import create_employee, create_love


def test_create_love(gae_testbed):
    """Test creating a basic Love instance"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="Great job on the project!",
        secret=False
    )

    assert love.sender_key == sender.key
    assert love.recipient_key == recipient.key
    assert love.message == "Great job on the project!"
    assert not love.secret
    assert isinstance(love.timestamp, datetime)
    assert love.company_values == []


def test_seconds_since_epoch(gae_testbed):
    """Test the seconds_since_epoch property"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="Test message"
    )

    expected_seconds = int(mktime(love.timestamp.timetuple()))
    assert love.seconds_since_epoch == expected_seconds


@mock.patch('loveapp.models.love.config')
def test_emote_with_matching_message(mock_love_config, gae_testbed):
    """Test emote property returns correct emoji when message matches"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    mock_love_config.MESSAGE_EMOTES = {
        'great': '👍',
        'awesome': '🎉'
    }

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="You did a GREAT job!"
    )

    assert love.emote == '👍'


@mock.patch('loveapp.models.love.config')
def test_emote_with_no_matching_message(mock_love_config, gae_testbed):
    """Test emote property returns None when no message matches"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    mock_love_config.MESSAGE_EMOTES = {
        'great': '👍',
        'awesome': '🎉'
    }

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="You did a good job!"
    )

    assert love.emote is None


def test_emote_with_none_message(gae_testbed):
    """Test emote property handles None message"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message=None
    )

    assert love.emote is None


def test_love_with_company_values(gae_testbed):
    """Test creating Love with company values"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')
    company_values = ['Integrity', 'Innovation']

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="Great demonstration of our values!",
        company_values=company_values
    )

    assert love.company_values == company_values


def test_secret_love_default_value(gae_testbed):
    """Test that secret defaults to False"""
    sender = create_employee(username='sender')
    recipient = create_employee(username='recipient')

    love = create_love(
        sender_key=sender.key,
        recipient_key=recipient.key,
        message="Test message"
    )

    assert not love.secret 