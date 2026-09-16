import frappe


def aggregate(doctype, filters, *fields):
	"""Run aggregate functions (Sum / Avg / Count from frappe.query_builder.functions)
	against `doctype` with ordinary dict filters.

	Frappe v16 rejects SQL functions passed as strings to frappe.db.get_value
	("sum(field)" raises ValidationError), while the query builder accepts function
	objects on both v15 and v16. Returns the first result row as a tuple with one
	value per field (aggregates without GROUP BY always yield exactly one row).
	"""
	rows = frappe.qb.get_query(doctype, filters=filters, fields=list(fields)).run()
	return rows[0] if rows else (None,) * len(fields)


def aggregate_rows(doctype, filters, fields, group_by):
	"""GROUP BY variant of aggregate(): `fields` mixes plain column names (str) and
	function objects carrying an alias (e.g. Sum(so.base_grand_total).as_("value")).
	Returns a list of dicts keyed by column name / alias, like frappe.get_all.

	Frappe v16 routes frappe.get_all through the same validator, so
	fields=["sum(x) as value"] fails there too; this keeps one code path for both.
	"""
	return frappe.qb.get_query(doctype, filters=filters, fields=fields, group_by=group_by).run(
		as_dict=True
	)
