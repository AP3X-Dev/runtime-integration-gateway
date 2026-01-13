const Stripe = require('stripe');

function rigPack() {
  return { name: "@rig/pack-stripe", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "stripe.customers.create",
      description: "Create a new Stripe customer",
      input_schema: {
        type: "object",
        properties: {
          email: { type: "string", description: "Customer email" },
          name: { type: "string", description: "Customer name" },
          phone: { type: "string", description: "Customer phone" },
          metadata: { type: "object", description: "Additional metadata" }
        },
        required: ["email"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" },
          email: { type: "string" },
          name: { type: "string" }
        },
        required: ["id"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["STRIPE_API_KEY"],
      risk_class: "write",
      tags: ["payments", "stripe"]
    },
    {
      name: "stripe.customers.search",
      description: "Search for Stripe customers",
      input_schema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query (e.g., email:'test@example.com')" }
        },
        required: ["query"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          customers: { type: "array" },
          has_more: { type: "boolean" }
        },
        required: ["customers"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["STRIPE_API_KEY"],
      risk_class: "read",
      tags: ["payments", "stripe"]
    },
    {
      name: "stripe.invoices.create",
      description: "Create a new Stripe invoice",
      input_schema: {
        type: "object",
        properties: {
          customer_id: { type: "string", description: "Customer ID" },
          collection_method: { type: "string", enum: ["charge_automatically", "send_invoice"] },
          days_until_due: { type: "integer", description: "Days until due" }
        },
        required: ["customer_id"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" },
          status: { type: "string" },
          total: { type: "integer" },
          currency: { type: "string" }
        },
        required: ["id"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["STRIPE_API_KEY"],
      risk_class: "money",
      tags: ["payments", "stripe"]
    },
    {
      name: "stripe.invoice_items.create",
      description: "Add an item to a Stripe invoice",
      input_schema: {
        type: "object",
        properties: {
          customer_id: { type: "string" },
          amount: { type: "integer", description: "Amount in cents" },
          currency: { type: "string", default: "usd" },
          description: { type: "string" },
          invoice_id: { type: "string" }
        },
        required: ["customer_id", "amount"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" },
          amount: { type: "integer" }
        },
        required: ["id"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["STRIPE_API_KEY"],
      risk_class: "money",
      tags: ["payments", "stripe"]
    },
    {
      name: "stripe.payment_links.create",
      description: "Create a Stripe payment link",
      input_schema: {
        type: "object",
        properties: {
          line_items: { type: "array", description: "Line items for payment" },
          metadata: { type: "object" }
        },
        required: ["line_items"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" },
          url: { type: "string" },
          active: { type: "boolean" }
        },
        required: ["id", "url"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["STRIPE_API_KEY"],
      risk_class: "money",
      tags: ["payments", "stripe"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  const apiKey = context.auth?.STRIPE_API_KEY;
  if (!apiKey) {
    throw new Error("STRIPE_API_KEY not provided in context");
  }

  const stripe = new Stripe(apiKey);

  switch (toolName) {
    case "stripe.customers.create":
      const customer = await stripe.customers.create({
        email: args.email,
        name: args.name,
        phone: args.phone,
        metadata: args.metadata
      });
      return { id: customer.id, email: customer.email, name: customer.name };

    case "stripe.customers.search":
      const searchResult = await stripe.customers.search({ query: args.query });
      return { customers: searchResult.data, has_more: searchResult.has_more };

    case "stripe.invoices.create":
      const invoice = await stripe.invoices.create({
        customer: args.customer_id,
        collection_method: args.collection_method,
        days_until_due: args.days_until_due
      });
      return { id: invoice.id, status: invoice.status, total: invoice.total, currency: invoice.currency };

    case "stripe.invoice_items.create":
      const item = await stripe.invoiceItems.create({
        customer: args.customer_id,
        amount: args.amount,
        currency: args.currency || "usd",
        description: args.description,
        invoice: args.invoice_id
      });
      return { id: item.id, amount: item.amount };

    case "stripe.payment_links.create":
      const link = await stripe.paymentLinks.create({
        line_items: args.line_items,
        metadata: args.metadata
      });
      return { id: link.id, url: link.url, active: link.active };

    default:
      throw new Error(`tool not found: ${toolName}`);
  }
}

module.exports = { rigPack, rigTools, rigInvoke };

