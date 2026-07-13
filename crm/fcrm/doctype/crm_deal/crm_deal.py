# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.exchange_rate import get_exchange_rate
from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log
from crm.fcrm.doctype.utils import add_or_remove_lost_reason_section_in_sidepanel

# Data that must already be captured for a deal to reach a given pipeline stage.
# Each gate is keyed by the status it guards; moving a deal forward into (or past)
# that status requires every listed field — and every field of earlier gates — to
# be filled. The "step" label tells the user which stage form collects the data.
STAGE_GATES = [
    {
        "status": "Qualification",
        "step": "Capture Requirements",
        "fields": [
            ("product_category", "Product Category"),
            ("product_sub_category", "Sub-Category"),
            ("product_variant", "Variant"),
            ("pain_frequency", "Pain Frequency"),
            ("pain_severity", "Pain Severity"),
            ("decision_maker", "Decision Maker"),
        ],
    },
    {
        "status": "Tech Assignment",
        "step": "Initiate Trial / Qualify Opportunity",
        "fields": [
            ("opportunity_type", "Opportunity Type"),
            ("decision_maker_involved", "Decision Maker Involved"),
            ("decision_timeline", "Decision Timeline"),
            ("expected_monthly_volume", "Expected Monthly Volume"),
            ("deal_value", "Deal Value"),
            ("business_impact", "Business Impact"),
            ("business_priority", "Business Priority"),
            ("forecast_category", "Forecast Category"),
            ("technical_person", "Technical Person"),
        ],
    },
    {
        "status": "Demo/Making",
        "step": "Technical Response",
        "fields": [
            ("product_suggestions", "Product Suggestions"),
            ("application_notes", "Application Notes"),
        ],
    },
    {
        "status": "Evaluation Completed",
        "step": "Record Evaluation",
        "fields": [
            ("evaluation_start", "Evaluation Start"),
            ("evaluation_end", "Evaluation End"),
            ("technical_person", "Technical Person"),
            ("evaluation_observations", "Evaluation Observations"),
            ("customer_feedback", "Customer Feedback"),
            ("trial_outcome", "Trial Outcome"),
        ],
    },
    {
        "status": "Proposal/Quotation",
        "step": "Prepare for Quotation",
        "fields": [
            ("legal_name", "Legal / Registered Name"),
            ("gstin", "GSTIN"),
            ("billing_address", "Billing Address"),
        ],
    },
]


class CRMDeal(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from crm.fcrm.doctype.crm_contacts.crm_contacts import CRMContacts
        from crm.fcrm.doctype.crm_image_list.crm_image_list import CRMImageList
        from crm.fcrm.doctype.crm_operation_impact_select.crm_operation_impact_select import CRMOperationImpactSelect
        from crm.fcrm.doctype.crm_pain_point_select.crm_pain_point_select import CRMPainPointSelect
        from crm.fcrm.doctype.crm_product_suggestion.crm_product_suggestion import CRMProductSuggestion
        from crm.fcrm.doctype.crm_rolling_response_time.crm_rolling_response_time import CRMRollingResponseTime
        from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import CRMStatusChangeLog
        from frappe.types import DF

        annual_revenue: DF.Currency
        application_notes: DF.SmallText | None
        assign_to_tech_team: DF.Check
        assigned_tech_member: DF.Link | None
        assignment_notes: DF.SmallText | None
        billing_address: DF.Link | None
        business_impact: DF.Literal["", "Low", "Medium", "High", "Strategic"]
        business_priority: DF.Literal["", "P1", "P2", "P3"]
        close_timeline: DF.Literal["", "Immediate (<1 month)", "Short (<2 months)", "Medium (3-6 months)"]
        closed_date: DF.Date | None
        communication_status: DF.Link | None
        contact: DF.Link | None
        contacts: DF.Table[CRMContacts]
        conversion_reason: DF.Literal["", "New product or application \u2014 first time enquiry", "Existing customer wants to try a different product", "Problem identified \u2014 needs technical recommendation", "Trial requested by customer"]
        credit_check: DF.Check
        currency: DF.Link | None
        current_monthly_spend: DF.Currency
        current_monthly_volume: DF.Float
        current_supplier: DF.Literal["", "Indian Supplier", "Imported", "In-house", "None / New"]
        customer_feedback: DF.SmallText | None
        customer_validation_received: DF.Check
        dc_delivery_lead_time: DF.Check
        dc_performance_colour: DF.Check
        dc_performance_metal_loss: DF.Check
        dc_price_competitive: DF.Check
        deal_owner: DF.Link | None
        deal_value: DF.Currency
        decision_maker: DF.Link | None
        decision_maker_involved: DF.Literal["", "Yes \u2014 Strong Deal", "Partial", "No"]
        decision_timeline: DF.Literal["", "Immediate (<1 month)", "Short (<2 months)", "Medium (3-6 months)", "Long (6 months+)"]
        email: DF.Data | None
        evaluation_end: DF.Date | None
        evaluation_observations: DF.SmallText | None
        evaluation_photos: DF.Table[CRMImageList]
        evaluation_start: DF.Date | None
        exchange_rate: DF.Float
        expected_closure_date: DF.Date | None
        expected_deal_value: DF.Currency
        expected_monthly_revenue: DF.Currency
        expected_monthly_volume: DF.Float
        expected_monthly_volume_uom: DF.Link | None
        first_name: DF.Data | None
        first_responded_on: DF.Datetime | None
        first_response_time: DF.Duration | None
        forecast_category: DF.Literal["", "Pipeline", "Best Case", "Commit", "Omitted"]
        freight_terms: DF.Literal["", "To Pay", "Charged", "Paid Upfront"]
        gender: DF.Link | None
        gstin: DF.Data | None
        impact_notes: DF.SmallText | None
        industry: DF.Link | None
        info_questions: DF.SmallText | None
        job_title: DF.Data | None
        last_name: DF.Data | None
        last_responded_on: DF.Datetime | None
        last_response_time: DF.Duration | None
        lead: DF.Link | None
        lead_name: DF.Data | None
        legal_name: DF.Data | None
        lost_notes: DF.SmallText | None
        lost_reason: DF.Link | None
        manager_reviewed: DF.Check
        mobile_no: DF.Data | None
        monthly_volume_uplift: DF.Float
        naming_series: DF.Literal["CRM-DEAL-.YYYY.-"]
        next_step: DF.Data | None
        no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
        not_suitable: DF.Check
        not_suitable_notes: DF.SmallText | None
        not_suitable_reason: DF.Literal["", "No matching product for required spec", "Spec outside our range", "Volume too low to serve", "Better served by alternative product", "Technically not feasible"]
        operational_impacts: DF.TableMultiSelect[CRMOperationImpactSelect]
        opportunity_type: DF.Literal["", "New Business", "New Product", "Expansion", "Win-back"]
        organization: DF.Link
        organization_name: DF.Data | None
        other_operational_impact: DF.Data | None
        other_pain_point: DF.Data | None
        pain_frequency: DF.Literal["", "Every Production Cycle", "Weekly", "Monthly", "Occasional"]
        pain_points: DF.TableMultiSelect[CRMPainPointSelect]
        pain_severity: DF.Literal["", "Critical", "High", "Medium", "Low"]
        performance_baseline: DF.Data | None
        performance_trial: DF.Data | None
        phone: DF.Data | None
        probability: DF.Percent
        product_category: DF.Link | None
        product_suggestions: DF.Table[CRMProductSuggestion]
        product_sub_category: DF.Link | None
        product_variant: DF.Link | None
        repeat_deal: DF.Check
        requirement_note: DF.SmallText | None
        response_by: DF.Datetime | None
        rolling_responses: DF.Table[CRMRollingResponseTime]
        sales_manager_approval_required: DF.Check
        sales_manager_approved: DF.Check
        salutation: DF.Link | None
        shipping_address: DF.Link | None
        sla: DF.Link | None
        sla_creation: DF.Datetime | None
        sla_status: DF.Literal["", "First Response Due", "Rolling Response Due", "Failed", "Fulfilled"]
        source: DF.Link | None
        status: DF.Link
        status_change_log: DF.Table[CRMStatusChangeLog]
        technical_person: DF.Link | None
        technical_response: DF.Literal["", "Recommend & Approve", "Request More Info", "Not Suitable"]
        territory: DF.Link
        testimonial_captured: DF.Check
        trial_outcome: DF.Literal["", "Successful", "Partial", "Unsuccessful"]
        trial_required: DF.Check
        trial_required_before_decision: DF.Check
        website: DF.Data | None

    # end: auto-generated types

    def before_validate(self):
        self.set_sla()

    def validate(self):
        self.validate_status()
        self.set_business_impact_metrics()
        self.set_primary_contact()
        self.set_primary_email_mobile_no()
        if not self.is_new() and self.has_value_changed("deal_owner") and self.deal_owner:
            self.share_with_agent(self.deal_owner)
            self.assign_agent(self.deal_owner)
        if self.has_value_changed("status"):
            self.validate_stage_requirements()
            add_status_change_log(self)
            if frappe.db.get_value("CRM Deal Status", self.status, "type") == "Won":
                self.closed_date = frappe.utils.nowdate()
        self.validate_forecasting_fields()
        self.validate_lost_reason()
        self.update_exchange_rate()

    def after_insert(self):
        if self.deal_owner:
            if self.deal_owner != frappe.session.user:
                self.share_with_agent(self.deal_owner)
            self.assign_agent(self.deal_owner)

        from crm.api.sales_manager import auto_assign_by_territory

        auto_assign_by_territory(self)

    def before_save(self):
        self.apply_sla()

    def on_update(self):
        from crm.api.sales_manager import (
            notify_roles_on_status_change,
            notify_sales_manager_on_approval,
        )
        from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
            create_customer_in_erpnext,
        )

        create_customer_in_erpnext(self, "on_update")
        notify_sales_manager_on_approval(self)
        notify_roles_on_status_change(self)

    def validate_status(self):
        if self.is_new():
            # Repeat deals are created directly at the quotation stage, so they
            # skip the "must start at the first stage" rule.
            if self.repeat_deal:
                return
            # New deals start at the first pipeline stage (lowest position),
            # which is "Req. Discussion" in this setup.
            first_open = frappe.get_all(
                "CRM Deal Status",
                filters={"type": "Open"},
                order_by="position asc",
                pluck="name",
                limit=1,
            )
            first_open = first_open[0] if first_open else None
            if not self.status:
                self.status = first_open
            elif first_open and self.status != first_open:
                # TODO: allow creating directly in quotation status later.
                frappe.throw(
                    _("A new deal can only start in {0} status").format(frappe.bold(first_open))
                )

    def validate_stage_requirements(self):
        """Gate forward status changes on the data each stage needs.

        Moving a deal forward (to a higher-position status) requires every field of
        the target stage's gate — and of all earlier gates — to be filled. Moving
        back to an earlier status, or marking the deal Lost, is never blocked. If the
        data is already present, the status simply changes.
        """
        if not self.status:
            return
        # Regular new deals start at stage 1 (nothing to gate yet); repeat deals are
        # created at the quotation stage, so their quotation-and-later gates are
        # verified even on insert.
        if self.is_new() and not self.repeat_deal:
            return

        statuses = frappe.get_all("CRM Deal Status", fields=["name", "position", "label"])
        positions = {s.name: s.position for s in statuses}
        labels = {s.name: s.label or s.name for s in statuses}
        new_pos = positions.get(self.status)
        if new_pos is None:
            return

        # Never block losing a deal.
        if frappe.db.get_value("CRM Deal Status", self.status, "type") == "Lost":
            return

        old_status = frappe.db.get_value("CRM Deal", self.name, "status")
        old_pos = positions.get(old_status, 0)

        # Only validate forward moves; going back to a previous stage is allowed.
        if new_pos <= old_pos:
            return

        def is_filled(fieldname):
            value = self.get(fieldname)
            if isinstance(value, str):
                return bool(value.strip())
            if isinstance(value, (int, float)):
                return value != 0
            return bool(value)

        # Repeat deals start at the quotation stage; only the data the earlier
        # stages (before Proposal/Quotation) would collect is skipped. The
        # quotation gate and any later gates are still enforced.
        quotation_pos = positions.get("Proposal/Quotation")

        missing_sections = []
        for gate in STAGE_GATES:
            gate_pos = positions.get(gate["status"])
            if gate_pos is None or gate_pos > new_pos:
                continue
            if self.repeat_deal and quotation_pos and gate_pos < quotation_pos:
                continue
            # No trial required → the evaluation isn't recorded, so its gate doesn't apply.
            if gate["status"] == "Evaluation Completed" and not self.trial_required:
                continue
            missing = []
            for fieldname, label in gate["fields"]:
                # Technical Person is only needed when the deal is assigned to the tech team.
                if fieldname == "technical_person" and not self.assign_to_tech_team:
                    continue
                if fieldname == "product_suggestions":
                    if not self.has_valid_product_suggestions():
                        missing.append(_(label))
                    continue
                if not is_filled(fieldname):
                    missing.append(_(label))
            if gate["status"] == "Proposal/Quotation" and not self.get_linked_customer():
                missing.append(_("Customer in ERPNext on the connected Organization"))
            if missing:
                missing_sections.append((labels.get(gate["status"], gate["status"]), missing))

        if not missing_sections:
            return

        lines = [
            "<b>{0}</b>: {1}".format(status_label, ", ".join(fields))
            for status_label, fields in missing_sections
        ]
        frappe.throw(
            _("This deal can't move to <b>{0}</b> until the following details are filled in:").format(
                labels.get(self.status, self.status)
            )
            + "<br><br>"
            + "<br>".join(lines),
            title=_("Incomplete stage details"),
        )

    def get_linked_customer(self):
        if not self.organization:
            return None
        return frappe.db.get_value("CRM Organization", self.organization, "erpnext_customer")

    def has_valid_product_suggestions(self):
        if not self.product_suggestions:
            return False
        for row in self.product_suggestions:
            if not row.item or frappe.utils.flt(row.quantity) <= 0:
                return False
        return True

    def set_primary_contact(self, contact=None):
        if not self.contacts:
            return

        if not contact and len(self.contacts) == 1:
            self.contacts[0].is_primary = 1
        elif contact:
            for d in self.contacts:
                if d.contact == contact:
                    d.is_primary = 1
                else:
                    d.is_primary = 0

    def set_primary_email_mobile_no(self):
        if not self.contacts:
            self.email = ""
            self.mobile_no = ""
            self.phone = ""
            return

        if len([contact for contact in self.contacts if contact.is_primary]) > 1:
            frappe.throw(_("Only one {0} can be set as primary.").format(frappe.bold("Contact")))

        primary_contact_exists = False
        for d in self.contacts:
            if d.is_primary == 1:
                primary_contact_exists = True
                self.email = d.email.strip() if d.email else ""
                self.mobile_no = d.mobile_no.strip() if d.mobile_no else ""
                self.phone = d.phone.strip() if d.phone else ""
                break

        if not primary_contact_exists:
            self.email = ""
            self.mobile_no = ""
            self.phone = ""

    def assign_agent(self, agent):
        if not agent:
            return

        assignees = self.get_assigned_users()
        if assignees:
            for assignee in assignees:
                if agent == assignee:
                    # the agent is already set as an assignee
                    return

        from crm.utils import assign_to_agent

        assign_to_agent("CRM Deal", self.name, agent)

    def share_with_agent(self, agent):
        if not agent:
            return

        docshares = frappe.get_all(
            "DocShare",
            filters={"share_name": self.name, "share_doctype": self.doctype},
            fields=["name", "user"],
        )

        shared_with = [d.user for d in docshares] + [agent]

        for user in shared_with:
            if user == agent and not frappe.db.exists(
                "DocShare",
                {"user": agent, "share_name": self.name, "share_doctype": self.doctype},
            ):
                frappe.share.add_docshare(
                    self.doctype,
                    self.name,
                    agent,
                    write=1,
                    flags={"ignore_share_permission": True},
                )
            elif user != agent:
                frappe.share.remove(
                    self.doctype,
                    self.name,
                    user,
                    flags={"ignore_share_permission": True, "ignore_permissions": True},
                )

    def set_sla(self):
        """
        Find an SLA to apply to the deal.
        """
        if self.sla:
            return

        sla = get_sla(self)
        if not sla:
            self.first_responded_on = None
            self.first_response_time = None
            return
        self.sla = sla.name

    def apply_sla(self):
        """
        Apply SLA if set.
        """
        if not self.sla:
            return
        sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
        if sla:
            sla.apply(self)

    def update_closed_date(self):
        """
        Update the closed date based on the "Won" status.
        """
        if self.status == "Won" and not self.closed_date:
            self.closed_date = frappe.utils.nowdate()

    def update_default_probability(self):
        """
        Update the default probability based on the status.
        """
        if not self.probability or self.probability == 0:
            self.probability = frappe.db.get_value("CRM Deal Status", self.status, "probability") or 0

    def update_expected_deal_value(self):
        """
        Update the expected deal value based on the net total or total.
        """
        if (
            frappe.db.get_single_value("FCRM Settings", "auto_update_expected_deal_value")
            and (self.net_total or self.total)
            and self.expected_deal_value
        ):
            self.expected_deal_value = self.net_total or self.total

    def validate_forecasting_fields(self):
        self.update_closed_date()
        self.update_default_probability()
        self.update_expected_deal_value()
        if frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
            if not self.expected_deal_value or self.expected_deal_value == 0:
                frappe.throw(_("Expected deal value is required."), frappe.MandatoryError)
            if not self.expected_closure_date:
                frappe.throw(_("Expected closure date is required."), frappe.MandatoryError)

    def set_business_impact_metrics(self):
        expected_volume = self.get("expected_monthly_volume") or 0
        current_volume = self.get("current_monthly_volume") or 0
        self.monthly_volume_uplift = expected_volume - current_volume

    def validate_lost_reason(self):
        """
        Validate the lost reason if the status is set to "Lost".
        """
        if self.status and frappe.get_cached_value("CRM Deal Status", self.status, "type") == "Lost":
            if not self.lost_reason:
                frappe.throw(_("Please specify a reason for losing the deal."), frappe.ValidationError)
            elif self.lost_reason == "Other" and not self.lost_notes:
                frappe.throw(_("Please specify the reason for losing the deal."), frappe.ValidationError)
        if self.has_value_changed("status"):
            add_or_remove_lost_reason_section_in_sidepanel(self)

    def update_exchange_rate(self):
        if self.has_value_changed("currency") or not self.exchange_rate:
            system_currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
            exchange_rate = 1
            if self.currency and self.currency != system_currency:
                exchange_rate = get_exchange_rate(self.currency, system_currency)

            self.db_set("exchange_rate", exchange_rate)

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Organization",
                "type": "Link",
                "key": "organization",
                "options": "CRM Organization",
                "width": "11rem",
            },
            {
                "label": "Annual Revenue",
                "type": "Currency",
                "key": "annual_revenue",
                "align": "right",
                "width": "9rem",
            },
            {
                "label": "Status",
                "type": "Link",
                "options": "CRM Deal Status",
                "key": "status",
                "width": "10rem",
            },
            {
                "label": "Email",
                "type": "Data",
                "key": "email",
                "width": "12rem",
            },
            {
                "label": "Mobile No.",
                "type": "Data",
                "key": "mobile_no",
                "width": "11rem",
            },
            {
                "label": "Assigned To",
                "type": "Text",
                "key": "_assign",
                "width": "10rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        rows = [
            "name",
            "organization",
            "annual_revenue",
            "status",
            "email",
            "currency",
            "mobile_no",
            "deal_owner",
            "sla_status",
            "response_by",
            "first_response_time",
            "first_responded_on",
            "modified",
            "_assign",
        ]
        return {"columns": columns, "rows": rows}

    @staticmethod
    def default_kanban_settings():
        return {
            "column_field": "status",
            "title_field": "organization",
            "kanban_fields": '["annual_revenue", "email", "mobile_no", "_assign", "modified"]',
        }


@frappe.whitelist()
def add_contact(deal: str, contact: str):
    if not frappe.has_permission("CRM Deal", "write", deal):
        frappe.throw(_("Not allowed to add contact to Deal"), frappe.PermissionError)

    deal = frappe.get_cached_doc("CRM Deal", deal)
    deal.append("contacts", {"contact": contact})
    deal.save()
    return True


@frappe.whitelist()
def remove_contact(deal: str, contact: str):
    if not frappe.has_permission("CRM Deal", "write", deal):
        frappe.throw(_("Not allowed to remove contact from Deal"), frappe.PermissionError)

    deal = frappe.get_cached_doc("CRM Deal", deal)
    deal.contacts = [d for d in deal.contacts if d.contact != contact]
    deal.save()
    return True


@frappe.whitelist()
def set_primary_contact(deal: str, contact: str):
    if not frappe.has_permission("CRM Deal", "write", deal):
        frappe.throw(_("Not allowed to set primary contact for Deal"), frappe.PermissionError)

    deal = frappe.get_cached_doc("CRM Deal", deal)
    deal.set_primary_contact(contact)
    deal.save()
    return True


def create_organization(doc):
    if not doc.get("organization_name"):
        return

    existing_organization = frappe.db.exists(
        "CRM Organization", {"organization_name": doc.get("organization_name")}
    )
    if existing_organization:
        return existing_organization

    organization = frappe.new_doc("CRM Organization")
    organization.update(
        {
            "organization_name": doc.get("organization_name"),
            "website": doc.get("website"),
            "territory": doc.get("territory"),
            "industry": doc.get("industry"),
            "annual_revenue": doc.get("annual_revenue"),
        }
    )
    organization.insert(ignore_permissions=True)
    return organization.name


def contact_exists(doc):
    email_exist = frappe.db.exists("Contact Email", {"email_id": doc.get("email")})
    mobile_exist = frappe.db.exists("Contact Phone", {"phone": doc.get("mobile_no")})

    doctype = "Contact Email" if email_exist else "Contact Phone"
    name = email_exist or mobile_exist

    if name:
        return frappe.db.get_value(doctype, name, "parent")

    return False


def create_contact(doc):
    existing_contact = contact_exists(doc)
    if existing_contact:
        return existing_contact

    contact = frappe.new_doc("Contact")
    contact.update(
        {
            "first_name": doc.get("first_name"),
            "last_name": doc.get("last_name"),
            "salutation": doc.get("salutation"),
            "company_name": doc.get("organization") or doc.get("organization_name"),
            "gender": doc.get("gender"),
        }
    )

    if doc.get("email"):
        contact.append("email_ids", {"email_id": doc.get("email"), "is_primary": 1})

    if doc.get("mobile_no"):
        contact.append("phone_nos", {"phone": doc.get("mobile_no"), "is_primary_mobile_no": 1})

    contact.insert(ignore_permissions=True)
    contact.reload()  # load changes by hooks on contact

    return contact.name


@frappe.whitelist()
def create_deal(doc: dict):
    deal = frappe.new_doc("CRM Deal")

    contact = doc.get("contact")
    if not contact and (
        doc.get("first_name") or doc.get("last_name") or doc.get("email") or doc.get("mobile_no")
    ):
        contact = create_contact(doc)

    deal.update(
        {
            "organization": doc.get("organization") or create_organization(doc),
            "contacts": [{"contact": contact, "is_primary": 1}] if contact else [],
        }
    )

    doc.pop("organization", None)

    deal.update(doc)

    deal.insert(ignore_permissions=True)
    return deal.name


@frappe.whitelist()
def get_trialed_products(organization: str):
    """Distinct product selections from an organization's deals that reached the
    trial evaluation stage or later (excluding Lost) — i.e. already-trialed
    products eligible for a repeat order."""
    eval_pos = frappe.db.get_value("CRM Deal Status", "Evaluation Completed", "position")
    if not eval_pos:
        return []

    trialed_statuses = frappe.get_all(
        "CRM Deal Status",
        filters={"position": [">=", eval_pos], "type": ["!=", "Lost"]},
        pluck="name",
    )
    if not trialed_statuses:
        return []

    rows = frappe.get_all(
        "CRM Deal",
        filters={"organization": organization, "status": ["in", trialed_statuses]},
        fields=["product_category", "product_sub_category", "product_variant"],
        distinct=True,
    )
    return [r for r in rows if r.get("product_category")]
