const twilio = require('twilio');

function rigPack() {
  return { name: "@rig/pack-twilio", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "twilio.sms.send",
      description: "Send an SMS message via Twilio",
      input_schema: {
        type: "object",
        properties: {
          to: { type: "string", description: "Recipient phone number" },
          from_: { type: "string", description: "Sender phone number" },
          body: { type: "string", description: "Message body" }
        },
        required: ["to", "body"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          sid: { type: "string" },
          status: { type: "string" }
        },
        required: ["sid", "status"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
      risk_class: "write",
      tags: ["twilio", "sms"]
    },
    {
      name: "twilio.calls.create",
      description: "Create a phone call via Twilio",
      input_schema: {
        type: "object",
        properties: {
          to: { type: "string", description: "Recipient phone number" },
          from_: { type: "string", description: "Caller phone number" },
          url: { type: "string", description: "TwiML URL" },
          twiml: { type: "string", description: "TwiML content" }
        },
        required: ["to"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          sid: { type: "string" },
          status: { type: "string" }
        },
        required: ["sid", "status"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
      risk_class: "write",
      tags: ["twilio", "voice"]
    },
    {
      name: "twilio.calls.status",
      description: "Get the status of a Twilio call",
      input_schema: {
        type: "object",
        properties: {
          call_sid: { type: "string", description: "Call SID" }
        },
        required: ["call_sid"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          sid: { type: "string" },
          status: { type: "string" },
          duration: { type: "string" }
        },
        required: ["sid", "status"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
      risk_class: "read",
      tags: ["twilio", "voice"]
    },
    {
      name: "twilio.verify.start",
      description: "Start a verification via Twilio Verify",
      input_schema: {
        type: "object",
        properties: {
          service_sid: { type: "string", description: "Verify service SID" },
          to: { type: "string", description: "Phone/email to verify" },
          channel: { type: "string", enum: ["sms", "call", "email"] }
        },
        required: ["service_sid", "to"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          sid: { type: "string" },
          status: { type: "string" }
        },
        required: ["sid", "status"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
      risk_class: "write",
      tags: ["twilio", "verify"]
    },
    {
      name: "twilio.verify.check",
      description: "Check a verification code via Twilio Verify",
      input_schema: {
        type: "object",
        properties: {
          service_sid: { type: "string", description: "Verify service SID" },
          to: { type: "string", description: "Phone/email verified" },
          code: { type: "string", description: "Verification code" }
        },
        required: ["service_sid", "to", "code"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          status: { type: "string" },
          valid: { type: "boolean" }
        },
        required: ["status", "valid"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
      risk_class: "write",
      tags: ["twilio", "verify"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  const accountSid = context.auth?.TWILIO_ACCOUNT_SID;
  const authToken = context.auth?.TWILIO_AUTH_TOKEN;
  
  if (!accountSid || !authToken) {
    throw new Error("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required");
  }

  const client = twilio(accountSid, authToken);

  switch (toolName) {
    case "twilio.sms.send":
      const message = await client.messages.create({
        to: args.to,
        from: args.from_,
        body: args.body
      });
      return { sid: message.sid, status: message.status };

    case "twilio.calls.create":
      const call = await client.calls.create({
        to: args.to,
        from: args.from_,
        url: args.url,
        twiml: args.twiml
      });
      return { sid: call.sid, status: call.status };

    case "twilio.calls.status":
      const callStatus = await client.calls(args.call_sid).fetch();
      return { sid: callStatus.sid, status: callStatus.status, duration: callStatus.duration };

    case "twilio.verify.start":
      const verification = await client.verify.v2
        .services(args.service_sid)
        .verifications.create({
          to: args.to,
          channel: args.channel || "sms"
        });
      return { sid: verification.sid, status: verification.status };

    case "twilio.verify.check":
      const check = await client.verify.v2
        .services(args.service_sid)
        .verificationChecks.create({
          to: args.to,
          code: args.code
        });
      return { status: check.status, valid: check.status === "approved" };

    default:
      throw new Error(`tool not found: ${toolName}`);
  }
}

module.exports = { rigPack, rigTools, rigInvoke };

