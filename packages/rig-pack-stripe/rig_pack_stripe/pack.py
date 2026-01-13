"""Stripe pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_stripe.tools import (
    customers_create, customers_search,
    invoices_create, invoice_items_create,
    payment_links_create, refunds_create,
    subscriptions_create, subscriptions_cancel,
)


TOOL_DEFS = [
    ToolDef(
        name="stripe.customers.create",
        description="Create a new Stripe customer",
        input_schema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email"},
                "name": {"type": "string", "description": "Customer name"},
                "phone": {"type": "string", "description": "Customer phone"},
                "metadata": {"type": "object", "description": "Additional metadata"},
            },
            "required": ["email"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "email": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["id"],
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="write",
    ),
    ToolDef(
        name="stripe.customers.search",
        description="Search for Stripe customers",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g., email:'test@example.com')"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "customers": {"type": "array"},
                "has_more": {"type": "boolean"},
            },
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="read",
    ),
    ToolDef(
        name="stripe.invoices.create",
        description="Create a new Stripe invoice",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "collection_method": {"type": "string", "enum": ["charge_automatically", "send_invoice"]},
                "days_until_due": {"type": "integer", "description": "Days until due"},
            },
            "required": ["customer_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string"},
                "total": {"type": "integer"},
                "currency": {"type": "string"},
            },
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
    ToolDef(
        name="stripe.invoice_items.create",
        description="Add an item to a Stripe invoice",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount": {"type": "integer", "description": "Amount in cents"},
                "currency": {"type": "string", "default": "usd"},
                "description": {"type": "string"},
                "invoice_id": {"type": "string"},
            },
            "required": ["customer_id", "amount"],
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}, "amount": {"type": "integer"}},
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
    ToolDef(
        name="stripe.payment_links.create",
        description="Create a Stripe payment link",
        input_schema={
            "type": "object",
            "properties": {
                "line_items": {"type": "array", "description": "Line items for payment"},
                "metadata": {"type": "object"},
            },
            "required": ["line_items"],
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}, "url": {"type": "string"}, "active": {"type": "boolean"}},
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
    ToolDef(
        name="stripe.refunds.create",
        description="Create a Stripe refund",
        input_schema={
            "type": "object",
            "properties": {
                "payment_intent": {"type": "string", "description": "Payment intent ID"},
                "charge": {"type": "string", "description": "Charge ID (alternative to payment_intent)"},
                "amount": {"type": "integer", "description": "Amount to refund (optional, full refund if omitted)"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}, "status": {"type": "string"}, "amount": {"type": "integer"}},
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
    ToolDef(
        name="stripe.subscriptions.create",
        description="Create a Stripe subscription",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "price_id": {"type": "string", "description": "Price ID"},
                "trial_days": {"type": "integer", "description": "Trial period in days"},
            },
            "required": ["customer_id", "price_id"],
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}, "status": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
    ToolDef(
        name="stripe.subscriptions.cancel",
        description="Cancel a Stripe subscription",
        input_schema={
            "type": "object",
            "properties": {
                "subscription_id": {"type": "string", "description": "Subscription ID to cancel"},
            },
            "required": ["subscription_id"],
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}, "status": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["STRIPE_API_KEY"],
        risk_class="money",
    ),
]

# Map tool names to implementations
TOOL_IMPLS = {
    "stripe.customers.create": customers_create,
    "stripe.customers.search": customers_search,
    "stripe.invoices.create": invoices_create,
    "stripe.invoice_items.create": invoice_items_create,
    "stripe.payment_links.create": payment_links_create,
    "stripe.refunds.create": refunds_create,
    "stripe.subscriptions.create": subscriptions_create,
    "stripe.subscriptions.cancel": subscriptions_cancel,
}


@dataclass
class StripePack:
    name: str = "rig-pack-stripe"
    version: str = "0.1.0"

    def rig_pack_metadata(self) -> Dict[str, str]:
        return {"name": self.name, "version": self.version}

    def rig_tools(self) -> List[ToolDef]:
        return TOOL_DEFS

    def rig_impls(self) -> Dict[str, RegisteredTool]:
        result = {}
        for tool in TOOL_DEFS:
            if tool.name in TOOL_IMPLS:
                result[tool.name] = RegisteredTool(
                    tool=tool,
                    impl=TOOL_IMPLS[tool.name],
                    pack=self.name,
                    pack_version=self.version,
                )
        return result


PACK = StripePack()

