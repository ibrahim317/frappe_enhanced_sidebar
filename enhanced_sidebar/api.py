# Copyright (c) 2025, Ibrahim Aboelsoud and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_sidebar_menu_items():
	"""
	Retrieves sidebar menu items categorized by their respective sidebar categories.
	Filters both categories and menu items based on the current user's roles.
	If a category is not permitted, its items are hidden regardless of item-level permissions.

	:return: A dictionary containing sidebar categories as keys and a list of their corresponding menu items as values.
	"""
	user_roles = frappe.get_roles(frappe.session.user)

	def is_permitted(doctype, parent_name):
		"""Returns True if the user has permission based on permitted_roles child table.
		If no roles are set, it's accessible to everyone.
		"""
		permitted_roles = frappe.get_all(
			"Has Role",
			filters={"parent": parent_name, "parenttype": doctype},
			pluck="role",
		)
		return not permitted_roles or any(role in user_roles for role in permitted_roles)

	sidebar_categories = frappe.get_all(
     	"Sidebar Category",
      	fields=["name", "category_name", "idx"],
    )

	# Initialize a dictionary to store the categorized menu items
	categorized_menu_items = {}

	# Iterate through each sidebar category
	for category in sorted(sidebar_categories, key=lambda x: x.idx):
		# Skip category AND all its items if user doesn't have category-level permission
		if not is_permitted("Sidebar Category", category.name):
			continue

		# Category is permitted — now fetch and filter its menu items
		sidebar_menu_items = frappe.get_all(
			"Sidebar Menu Item",
			filters={"category": category.name},
			fields=["name", "name1", "route", "url", "icon", "custom_icon", "use_custom_icon", "link_to", "idx"],
			order_by="idx",
		)

		permitted_menu_items = [
			item for item in sidebar_menu_items if is_permitted("Sidebar Menu Item", item.name)
		]

		if permitted_menu_items:
			categorized_menu_items[category.category_name] = permitted_menu_items

	# Fetch uncategorized items (no category = not under any category restriction)
	# so only item-level permission applies here
	uncategorized_items = frappe.get_all(
		"Sidebar Menu Item",
		filters={"category": ("is", "not set")},
		fields=["name", "name1", "route", "url", "icon", "custom_icon", "use_custom_icon", "link_to", "idx"],
		order_by="idx"
	)

	permitted_uncategorized_items = [
		item for item in uncategorized_items if is_permitted("Sidebar Menu Item", item.name)
	]

	if permitted_uncategorized_items:
		if "General" in categorized_menu_items:
			categorized_menu_items["General"].extend(permitted_uncategorized_items)
		else:
			categorized_menu_items["General"] = permitted_uncategorized_items

	return categorized_menu_items
