# -*- coding: utf-8 -*-
from collections import Counter
from collections import defaultdict

import yaml

REMOTE_OFFICE = 'Remote'
OTHER_OFFICE = 'Other'


def get_all_offices():
    from loveapp.models import Employee

    """
    Retrieve all the offices in the database
    Returns: List[str]
    """
    return [
        row.office
        for row in Employee.query(projection=['office'], distinct=True).fetch() if row.office
    ]


class OfficeParser:
    def __init__(self, employee_dicts=None):
        """

        Args:
            employee_dicts ([Dict], optional): Defaults to None.
            If this dict exists the location of the employee will be determined from
            the team location in case we don't have a location assigned to the employee
        """
        self.offices = yaml.safe_load(open('offices.yaml'))
        self.__team_country_map = None
        if employee_dicts:
            self.__team_country_map = self.__create_team_country_map(employee_dicts)

    def __create_team_country_map(self, employee_dicts):
        """

        Args:
            employee_dicts ([Dict]): employee info

        Returns:
            [DICT]: Map of each team and the country assigned to it.
            The team country is the country with more employees.
        """
        teams_locations = defaultdict(lambda: Counter())
        for employee in employee_dicts:
            teams_locations[employee['department']][
                self.__get_office_name_match(employee['office'])
            ] += 1

        team_country_map = {}
        for team, countries in teams_locations.items():
            team_country_map[team] = countries.most_common(1)[0][0]

        return team_country_map

    def get_office_name(self, employee_office_location, employee_department=None):
        """
        Given the employee office location retrieve the office name
        The matching is done by basic string matching
        Args:
            employee_office_location: str
            employee_department: Optional[str].
                This is the team of the employee. If it exists the office will be guessed from the
                office location in case we don't have an office for the employee
            Returns: str

        Examples in: out
            if we have yaml file with the follwong content: {Hamburg office, SF office}
            NY Remote: Remote
            SF office: SF office
            SF office Remote: SF office
            Germany Hamburg office: Hamburg office
            CA SF New Montgomery Office: Sf office
        """
        employee_office_location = employee_office_location.lower()

        matched_office_name = self.__get_office_name_match(employee_office_location)
        if matched_office_name != employee_office_location:
            return matched_office_name

        if self.__team_country_map and employee_department:
            return self.get_office_name(self.__team_country_map[employee_department])

        if REMOTE_OFFICE.lower() in employee_office_location:
            return REMOTE_OFFICE

        return OTHER_OFFICE

    def __get_office_name_match(self, office_name):
        """
        Get the office name in the saved yaml file that matches this office name
        Args:
            office_name [str]

        Returns:
            [str]: The matched office name if exists otherwise the same name in the input
        """
        for office in self.offices:
            if office.lower() in office_name.lower():
                return office
        return office_name
