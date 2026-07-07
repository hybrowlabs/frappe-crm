import frappe
from frappe.utils import add_days, flt, get_datetime, getdate, now_datetime

# Account Executive ("My Dashboard") — everything is scoped to the logged-in
# salesperson (frappe.session.user): my open deals, my tasks, my accounts, my
# performance. Computed live from CRM Deal / Task / Lead / Organization and
# ERPNext Sales Orders. No mock data; a metric with no source is omitted.


def _has_sales_order():
	return frappe.db.exists("DocType", "Sales Order")


def _open_statuses():
	return [
		s.name
		for s in frappe.get_all(
			"CRM Deal Status",
			filters={"type": ["in", ["Open", "Ongoing"]]},
			fields=["name", "position"],
			order_by="position",
		)
	]


def _value(d):
	return flt(d.deal_value) or flt(d.annual_revenue)


def _pipeline(me, statuses):
	filters = {"deal_owner": me}
	if statuses:
		filters["status"] = ["in", statuses]
	deals = frappe.get_all(
		"CRM Deal",
		filters=filters,
		fields=["name", "organization", "organization_name", "status", "deal_value", "annual_revenue", "product_category"],
	)
	by_stage = []
	for name in statuses:
		group = [d for d in deals if d.status == name]
		if group:
			by_stage.append({"stage": name, "count": len(group), "value": sum(_value(d) for d in group)})
	deal_rows = [
		{
			"name": d.name,
			"organization": d.organization,
			"organization_name": d.organization_name or d.organization,
			"stage": d.status,
			"category": d.product_category,
			"value": _value(d),
		}
		for d in deals
	]
	return {
		"by_stage": by_stage,
		"total_value": sum(_value(d) for d in deals),
		"total_count": len(deals),
		"deals": deal_rows,
	}


def _tasks(me):
	now = now_datetime()
	today = getdate()
	rows = frappe.get_all(
		"CRM Task",
		filters={"assigned_to": me, "status": ["in", ["Backlog", "Todo", "In Progress"]]},
		fields=["name", "title", "due_date", "priority", "reference_doctype", "reference_docname", "status"],
	)
	today_tasks, overdue = [], []
	for r in rows:
		item = {
			"name": r.name,
			"title": r.title,
			"priority": r.priority,
			"reference_doctype": r.reference_doctype,
			"reference_docname": r.reference_docname,
			"due_date": r.due_date,
		}
		if not r.due_date:
			continue
		due = get_datetime(r.due_date)
		if getdate(due) == today:
			today_tasks.append(item)
		elif due < now:
			item["days"] = (today - getdate(due)).days
			overdue.append(item)
	overdue.sort(key=lambda t: t.get("days", 0), reverse=True)

	# My deals awaiting a technical-team response.
	pending = frappe.get_all(
		"CRM Deal",
		filters={"deal_owner": me, "assign_to_tech_team": 1, "evaluation_end": ["is", "not set"]},
		fields=["name", "organization", "organization_name", "evaluation_start", "creation"],
	)
	pending_tech = []
	for p in pending:
		start = get_datetime(p.evaluation_start) if p.evaluation_start else get_datetime(p.creation)
		hours = round((now - start).total_seconds() / 3600, 1)
		pending_tech.append(
			{
				"name": p.name,
				"organization": p.organization,
				"organization_name": p.organization_name or p.organization,
				"elapsed_hours": hours,
			}
		)
	pending_tech.sort(key=lambda t: t["elapsed_hours"], reverse=True)

	return {
		"today": today_tasks,
		"today_count": len(today_tasks),
		"overdue": overdue[:25],
		"overdue_count": len(overdue),
		"pending_tech": pending_tech[:25],
		"pending_tech_count": len(pending_tech),
	}


def _accounts(me):
	today = getdate()
	orgs = frappe.get_all(
		"CRM Organization",
		filters={"account_owner": me},
		fields=["name", "organization_name", "last_order", "modified"],
	)
	last_contact, dormant30, no_recent = [], [], []
	for o in orgs:
		contact_days = (today - getdate(o.modified)).days
		last_contact.append(
			{
				"organization": o.name,
				"organization_name": o.organization_name or o.name,
				"contact_days": contact_days,
			}
		)
		if o.last_order:
			days = (today - getdate(o.last_order)).days
			if days > 30:
				dormant30.append(
					{
						"organization": o.name,
						"organization_name": o.organization_name or o.name,
						"last_order": o.last_order,
						"days": days,
					}
				)
		if contact_days > 14:
			no_recent.append(
				{
					"organization": o.name,
					"organization_name": o.organization_name or o.name,
					"contact_days": contact_days,
				}
			)
	last_contact.sort(key=lambda a: a["contact_days"], reverse=True)
	dormant30.sort(key=lambda a: a["days"], reverse=True)
	no_recent.sort(key=lambda a: a["contact_days"], reverse=True)
	return {
		"account_count": len(orgs),
		"last_contact": last_contact[:25],
		"dormant30": dormant30[:25],
		"dormant30_count": len(dormant30),
		"no_recent": no_recent[:25],
		"no_recent_count": len(no_recent),
	}


def _performance(me):
	today = getdate()
	month_start = today.replace(day=1)

	# Orders booked this month for my accounts (no target source → value only).
	orders_value = 0.0
	if _has_sales_order():
		my_customers = [
			o.erpnext_customer
			for o in frappe.get_all("CRM Organization", filters={"account_owner": me}, fields=["erpnext_customer"])
			if o.erpnext_customer
		]
		if my_customers:
			orders_value = flt(
				frappe.db.get_value(
					"Sales Order",
					{"docstatus": 1, "customer": ["in", my_customers], "transaction_date": ["between", [month_start, today]]},
					"sum(base_grand_total)",
				)
			)

	leads = frappe.get_all("CRM Lead", filters={"lead_owner": me}, fields=["converted"])
	leads_assigned = len(leads)
	leads_converted = sum(1 for l in leads if l.converted)

	trials = frappe.get_all(
		"CRM Deal",
		filters={"deal_owner": me, "trial_required": 1, "trial_outcome": ["in", ["Successful", "Partial", "Unsuccessful"]]},
		fields=["trial_outcome"],
	)
	trials_total = len(trials)
	trials_won = sum(1 for t in trials if t.trial_outcome == "Successful")

	return {
		"orders_this_month": orders_value,
		"has_orders": _has_sales_order(),
		"leads_assigned": leads_assigned,
		"leads_converted": leads_converted,
		"lead_conversion_rate": round(leads_converted / leads_assigned * 100) if leads_assigned else 0,
		"trials_total": trials_total,
		"trials_won": trials_won,
		"trial_conversion_rate": round(trials_won / trials_total * 100) if trials_total else 0,
	}


@frappe.whitelist()
def get_ae_dashboard() -> dict:
	"""My Dashboard for the logged-in account executive — pipeline, tasks,
	accounts and performance, all scoped to the session user. No mock data."""
	me = frappe.session.user
	statuses = _open_statuses()
	return {
		"user": me,
		"pipeline": _pipeline(me, statuses),
		"tasks": _tasks(me),
		"accounts": _accounts(me),
		"performance": _performance(me),
	}
