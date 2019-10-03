from pyramid.httpexceptions import HTTPForbidden
import pytest
from tests.incidents import BaseTest
from controllers.incidents.incident_controller import VICTIMS_TYPES

from common.data_framework.archive.entities.archive_patrol_shift import \
    ShiftEventTypes
from common.definitions.application_consts import UserType, AgencyType, \
    ReportSection


class TestAddIncident(BaseTest):
    victims_types_test_data = [(x, True) for x in VICTIMS_TYPES] + \
                              [('', None), (None, None)]

    properties_to_populate = (
        "description", "memo", "type", "category", "expenceType",
        "priority", "stage", "autoRemove"
    )

    # Test check status code of 'add_incident'- all users
    @pytest.mark.parametrize('user_type, expected',
                             [(UserType.FSP_DISPATCH.value, 201),
                              (UserType.FSP_PATROL.value, 201),
                              (UserType.POLICE_PATROL.value, 201),
                              (UserType.POLICE_DISPATCH.value, 201),
                              (UserType.TMC.value, 201),
                              (UserType.MNTC_PATROL.value, 201),
                              (UserType.MNTC_DISPATCH.value, 201)])
    def test_add_maintenance(
            self,
            monkeypatch,
            maint_req,
            user_type,
            expected
    ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body['userType'] = user_type
        maint_req.user_type = maint_req.json_body['userType']

        def skip_command(BaseView, out_entity):
            pass

        monkeypatch.setattr(IncidentView, 'push_to_queue', skip_command)
        response = IncidentView(maint_req).add_incident()
        assert response.status_code == expected

    # Test check status code of 'add_incident' with/without `location`
    # For all users
    @pytest.mark.parametrize('location, expected',
                             [({'lat': 36.159076, 'lng': -115.323014}, 201),
                              (None, 422)])
    def test_no_location(
            self,
            monkeypatch,
            maint_req,
            location,
            expected
    ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.user_type = maint_req.json_body['userType']
        maint_req.json_body['incidentDetails']['location'] = location

        def skip_command(BaseView, out_entity):
            pass

        monkeypatch.setattr(IncidentView, 'push_to_queue', skip_command)
        response = IncidentView(maint_req).add_incident()
        status_code = response.status_code
        assert status_code == expected

    # Test Report agency_type for all users
    @pytest.mark.parametrize(
        'user_type, expected',
        [(UserType.FSP_DISPATCH.value, ReportSection.FSP.value),
         (UserType.FSP_PATROL.value, ReportSection.FSP.value),
         (UserType.POLICE_PATROL.value, ReportSection.POLICE.value),
         (UserType.POLICE_DISPATCH.value, ReportSection.POLICE.value),
         (UserType.TMC.value, ReportSection.TMC.value),
         (UserType.MNTC_PATROL.value, ReportSection.MNTC.value),
         (UserType.MNTC_DISPATCH.value, ReportSection.MNTC.value)]
    )
    def test_report_by_report_sections(
            self,
            maint_req,
            user_type,
            expected
    ):
        from common.objects.report import Report
        maint_req.json_body['userType'] = user_type

        report = Report(
            maint_req.json_body,
            user_type=maint_req.json_body['userType']
        )

        assert report.agency_type == expected

    # Test Report user_type for all users
    @pytest.mark.parametrize(
        'user_type, expected',
        [(UserType.FSP_DISPATCH.value, UserType.FSP_DISPATCH.value),
         (UserType.FSP_PATROL.value, UserType.FSP_PATROL.value),
         (UserType.POLICE_PATROL.value, UserType.POLICE_PATROL.value),
         (UserType.POLICE_DISPATCH.value, UserType.POLICE_DISPATCH.value),
         (UserType.TMC.value, UserType.TMC.value),
         (UserType.MNTC_PATROL.value, UserType.MNTC_PATROL.value),
         (UserType.MNTC_DISPATCH.value, UserType.MNTC_DISPATCH.value)]
    )
    def test_report_by_user_types(
            self,
            maint_req,
            user_type,
            expected
    ):
        from common.objects.report import Report
        maint_req.json_body['userType'] = user_type

        report = Report(
            maint_req.json_body,
            user_type=maint_req.json_body['userType']
        )

        user_type = report.report_dict['userType']
        assert user_type == expected

    # Test user type is fsp -> tmc-mode on
    def test_add_incident_fsp_tmc_mode_on(
            self,
            monkeypatch,
            maint_req
    ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body['userType'] = UserType.FSP_DISPATCH.value
        maint_req.json_body['extendedData'] = ['tmc-mode']

        def compare_results(BaseView, out_entity):
            assert out_entity['payload']['metadata']['originalUserType'] == \
                AgencyType.FSP.value
            assert out_entity['payload']['metadata']['userType'] == \
                UserType.TMC.value

        monkeypatch.setattr(IncidentView, 'push_to_queue', compare_results)
        IncidentView(maint_req).add_incident()

    # Test victims if mitigation type in VICTIMS_TYPES
    @pytest.mark.parametrize(
        'victim_type, expected',
        victims_types_test_data
    )
    def test_victims_if_mitigation(
            self,
            monkeypatch,
            maint_req,
            victim_type,
            expected
    ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body['incidentDetails'][
            'fsp']['mitigations'] = [victim_type]

        def compare_results(BaseView, out_entity):
            assert out_entity['payload']['entity']['report'].get(
                'victims') == expected

        monkeypatch.setattr(IncidentView, 'push_to_queue', compare_results)
        IncidentView(maint_req).add_incident()

    # Test reporter by report_type `new-incident`-->set userId else user.H
    def test_check_reporter(
            self,
            monkeypatch,
            maint_req,
            user
    ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body['userType'] = UserType.FSP_DISPATCH.value

        def compare_results(BaseView, out_entity):
            reporter_h_types = [
                ShiftEventTypes.new_shell_incident.value,
                ShiftEventTypes.from_shell_incident.value,
                ShiftEventTypes.patrol_confirm_incident.value,
                ShiftEventTypes.patrol_mitigate_incident.value
            ]
            reporter_id_types = ['new-incident']
            report_type = out_entity['payload']['metadata']['reportType']
            reporter = out_entity['payload']['entity']['reporter']

            if report_type in reporter_id_types:
                assert reporter == user.user_id
            elif reporter_h_types:
                assert reporter == user.H

        monkeypatch.setattr(IncidentView, 'push_to_queue', compare_results)
        IncidentView(maint_req).add_incident()

    # Test sub agencies and all mandatory keys
    @pytest.mark.parametrize(
        'report_section,user_type',
        [(UserType.FSP_DISPATCH.value, ReportSection.FSP.value),
         (UserType.FSP_PATROL.value, ReportSection.FSP.value),
         (UserType.POLICE_PATROL.value, ReportSection.POLICE.value),
         (UserType.POLICE_DISPATCH.value, ReportSection.POLICE.value),
         (UserType.TMC.value, ReportSection.TMC.value),
         (UserType.MNTC_PATROL.value, ReportSection.MNTC.value),
         (UserType.MNTC_DISPATCH.value, ReportSection.MNTC.value)]
    )
    def test_other_agencies_report(self, maint_req, report_section, user_type):
        from common.objects.report import Report
        maint_req.json_body['userType'] = user_type
        report = Report(maint_req.json_body, user_type=user_type)

        for key in ReportSection:
            if key.value == report.agency_type:
                continue
            assert key.value in report.report_dict
            for prop in self.properties_to_populate:
                assert prop in report.report_dict[key.value]

    @pytest.mark.parametrize(
        'report_section, expected',
        [
            (ReportSection.POLICE.value, True),
            (ReportSection.MNTC.value, True),
            (ReportSection.FSP.value, True),
            (ReportSection.TMC.value, True)
        ]
    )
    def test_other_agencies_by_report_section(
            self,
            maint_req,
            report_section,
            expected
    ):
        from common.objects.report import Report
        report = Report(maint_req.json_body, report_section=report_section)

        for key in ReportSection:
            if key.value == report.agency_type:
                continue
            assert key.value in report.report_dict
            for prop in self.properties_to_populate:
                assert prop in report.report_dict[key.value]

    def test_wrong_user_req(self, monkeypatch, maint_req, ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body['userId'] = 'some_incorrect userId'
        maint_req.user_type = maint_req.json_body['userType']

        def skip_command(BaseView, out_entity):
            pass

        monkeypatch.setattr(IncidentView, 'push_to_queue', skip_command)
        with pytest.raises(HTTPForbidden) as exc_data:
            IncidentView(maint_req).add_incident()

        # Forbidden 403
        exc_info = exc_data.value.explanation
        assert "Access was denied to this resource." == exc_info

    def test_empty_req(self, monkeypatch, maint_req, ):
        from controllers.incidents.incident_controller import IncidentView
        maint_req.json_body = {}

        def skip_command(BaseView, out_entity):
            pass

        monkeypatch.setattr(IncidentView, 'push_to_queue', skip_command)
        with pytest.raises(HTTPForbidden) as exc_data:
            IncidentView(maint_req).add_incident()

        # Forbidden 403
        exc_info = exc_data.value.explanation
        assert "Access was denied to this resource." == exc_info
