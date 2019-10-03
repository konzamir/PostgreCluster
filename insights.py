from datetime import datetime

import factory
import pytest
import pytz
from factory import fuzzy
from tests.fixtures import BaseFactory, FuzzyList

from common.data_framework.archive.entities.insights\
    .archive_configuration import ArchiveConfiguration
from common.data_framework.archive.entities.insights.archive_insight import \
    ArchiveInsight
from common.data_framework.archive.entities.insights.archive_report import \
    ArchiveReport
from common.definitions.application_consts import AgencyType


class ReportFactory(BaseFactory):
    class Meta:
        model = ArchiveReport

    title = fuzzy.FuzzyText()
    description = fuzzy.FuzzyText()
    is_private = fuzzy.FuzzyChoice([True, False])
    is_deleted = fuzzy.FuzzyChoice([True, False])

    updated_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at_tz = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )

    owners = FuzzyList()
    favorites = FuzzyList()
    views = fuzzy.FuzzyInteger(low=0)
    is_locked = fuzzy.FuzzyText()
    agencies = [i.value for i in AgencyType]


class ConfigurationFactory(BaseFactory):
    class Meta:
        model = ArchiveConfiguration

    title = fuzzy.FuzzyText()

    is_deleted = fuzzy.FuzzyChoice([True, False])

    updated_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at_tz = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )

    report = factory.SubFactory(ReportFactory)
    incident_types = FuzzyList()
    insights = FuzzyList()
    sections = FuzzyList()
    path = FuzzyList()
    days = FuzzyList()
    hours = FuzzyList()
    units = FuzzyList()
    periods = FuzzyList()


class FuzzyStatsData(fuzzy.BaseFuzzyAttribute):
    def fuzz(self):
        return {"data": {}, "metric": {}, "code": "SUCCESS"}


class InsightFactory(BaseFactory):
    class Meta:
        model = ArchiveInsight

    title = fuzzy.FuzzyText()

    is_deleted = fuzzy.FuzzyChoice([True, False])

    updated_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )
    created_at_tz = fuzzy.FuzzyDateTime(
        datetime.utcnow().replace(tzinfo=pytz.UTC)
    )

    report = factory.SubFactory(ReportFactory)
    config = factory.SubFactory(ConfigurationFactory)

    type = fuzzy.FuzzyText()
    stats_data = FuzzyStatsData()
    incident_types = FuzzyList()
    sections = FuzzyList()
    path = FuzzyList()
    days = FuzzyList()
    hours = FuzzyList()
    units = FuzzyList()
    periods = FuzzyList()


class ConfigurationQueryFactory(factory.BaseDictFactory):
    class Meta:
        model = dict

    insights = FuzzyList()
    incidentTypes = FuzzyList()
    sections = FuzzyList()
    units = FuzzyList()
    path = FuzzyList()
    days = FuzzyList()
    hours = FuzzyList()
    periods = FuzzyList()


@pytest.fixture
def report():
    report = ReportFactory(
        is_deleted=False, is_locked='asd', is_private=False,
        agencies=[i.value for i in AgencyType]
    )
    yield report
    return report.force_delete()


@pytest.fixture
def report_configuration(report):
    from_date = datetime.utcnow().date().replace(day=1).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().date().replace(day=30).strftime('%Y-%m-%d')
    conf = ConfigurationFactory(
        incident_types=['ABANDONED-VEH'],
        insights=['AVG_INCIDENTS_NUMBER'],
        sections=['I-15 NB'],
        path=[{'lat': 0, 'lng': 1}],
        days=['Mon'],
        hours=[[0, 24]],
        units=['FSP-A'],
        periods=[[from_date, to_date]],
        report=report,
        is_deleted=False
    )
    yield conf
    conf.force_delete()


@pytest.fixture
def insight(report_configuration):
    from_date = datetime.utcnow().date().replace(day=1).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().date().replace(day=30).strftime('%Y-%m-%d')
    insight = InsightFactory(
        type='AVG_INCIDENTS_NUMBER',
        incident_types=['ABANDONED-VEH'],
        sections=['I-15 NB'],
        path=[{'lat': 0, 'lng': 1}],
        days=['Mon'],
        hours=[[0, 24]],
        units=['FSP-A'],
        periods=[[from_date, to_date]],
        config=report_configuration,
        report=report_configuration.report,
        is_deleted=False
    )
    yield insight
    insight.force_delete()
