#!/usr/bin/env node

/**
 * Helper script to exchange authorization code for token
 * Usage: node get-token.js YOUR_AUTH_CODE
 */

import { google } from "googleapis";
import fs from "fs/promises";

async function main() {
  const authCode = process.argv[2];

  if (!authCode) {
    console.error("Usage: node get-token.js YOUR_AUTH_CODE");
    process.exit(1);
  }

  try {
    const creds = JSON.parse(await fs.readFile("credentials.json", "utf8"));
    const credData = creds.web || creds.installed;

    const oAuth2Client = new google.auth.OAuth2(
      credData.client_id,
      credData.client_secret,
      credData.redirect_uris[0]
    );

    console.log("Exchanging code for token...");
    const { tokens } = await oAuth2Client.getToken(authCode);

    await fs.writeFile("token.json", JSON.stringify(tokens, null, 2));
    console.log("✓ Token saved to token.json");
    console.log("✓ You can now use the Google Meet MCP server");
  } catch (error) {
    console.error("Error:", error.message);
    process.exit(1);
  }
}

main();
