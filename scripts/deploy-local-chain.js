import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const CAST_BIN = process.env.CAST_BIN ?? "/home/respectthanh/.foundry/bin/cast";
const RPC_URL = process.env.RPC_URL ?? "http://127.0.0.1:8545";
const OWNER_PRIVATE_KEY =
  process.env.OWNER_PRIVATE_KEY ??
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const OPERATOR_PRIVATE_KEY =
  process.env.OPERATOR_PRIVATE_KEY ??
  "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d";
const ATTACKER_PRIVATE_KEY =
  process.env.ATTACKER_PRIVATE_KEY ??
  "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a";

const buildPath = path.join("build", "contracts", "TrustFaceChain.json");
const reportPath = path.join("reports", "local_chain_report.json");
const gasCsvPath = path.join("reports", "local_chain_gas.csv");

function main() {
  if (!fs.existsSync(buildPath)) {
    throw new Error("missing build/contracts/TrustFaceChain.json; run npm run compile:contracts first");
  }
  const contractBuild = JSON.parse(fs.readFileSync(buildPath, "utf8"));
  const owner = walletAddress(OWNER_PRIVATE_KEY);
  const operator = walletAddress(OPERATOR_PRIVATE_KEY);
  const attacker = walletAddress(ATTACKER_PRIVATE_KEY);

  const deployReceipt = send(["--private-key", OWNER_PRIVATE_KEY, "--create", contractBuild.bytecode]);
  const contractAddress = deployReceipt.contractAddress;
  if (!contractAddress) {
    throw new Error("deployment did not return a contract address");
  }

  const subjectId = bytes32("subject-demo-001");
  const templateCommitment = bytes32("template-demo-001");
  const consentHash = bytes32("consent-demo-001");
  const modelVersion = bytes32("arcface-r100-v1");
  const verificationHash = bytes32("verification-demo-001");
  const reasonHash = bytes32("operator revocation");

  const operatorReceipt = send([
    "--private-key",
    OWNER_PRIVATE_KEY,
    contractAddress,
    "setOperator(address,bool)",
    operator,
    "true",
  ]);

  let unauthorizedWriteBlocked = false;
  try {
    send([
      "--private-key",
      ATTACKER_PRIVATE_KEY,
      contractAddress,
      "enrollIdentity(bytes32,bytes32,bytes32,bytes32)",
      bytes32("attacker-subject"),
      templateCommitment,
      consentHash,
      modelVersion,
    ]);
  } catch {
    unauthorizedWriteBlocked = true;
  }

  const enrollReceipt = send([
    "--private-key",
    OPERATOR_PRIVATE_KEY,
    contractAddress,
    "enrollIdentity(bytes32,bytes32,bytes32,bytes32)",
    subjectId,
    templateCommitment,
    consentHash,
    modelVersion,
  ]);
  const verifyReceipt = send([
    "--private-key",
    OPERATOR_PRIVATE_KEY,
    contractAddress,
    "logVerification(bytes32,bytes32,bytes32,bool)",
    subjectId,
    verificationHash,
    modelVersion,
    "true",
  ]);
  const revokeReceipt = send([
    "--private-key",
    OPERATOR_PRIVATE_KEY,
    contractAddress,
    "revokeTemplate(bytes32,bytes32)",
    subjectId,
    reasonHash,
  ]);
  const revoked = call([contractAddress, "isRevoked(bytes32)(bool)", subjectId]).trim() === "true";

  const transactions = [
    tx("deploy", owner, deployReceipt),
    tx("setOperator", owner, operatorReceipt),
    tx("enrollIdentity", operator, enrollReceipt),
    tx("logVerification", operator, verifyReceipt),
    tx("revokeTemplate", operator, revokeReceipt),
  ];
  const totalGas = transactions.reduce((sum, item) => sum + item.gasUsed, 0);
  const report = {
    generatedAt: new Date().toISOString(),
    rpcUrl: RPC_URL,
    contractAddress,
    owner,
    operator,
    attacker,
    unauthorizedWriteBlocked,
    revoked,
    subjectId,
    totalGas,
    transactions,
  };

  fs.mkdirSync("reports", { recursive: true });
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  fs.writeFileSync(gasCsvPath, csv(transactions));
  console.log(JSON.stringify(report, null, 2));
}

function walletAddress(privateKey) {
  return execCast(["wallet", "address", "--private-key", privateKey]).trim();
}

function send(args) {
  const output = execCast(["send", "--rpc-url", RPC_URL, "--json", ...args]);
  return parseJson(output);
}

function call(args) {
  return execCast(["call", "--rpc-url", RPC_URL, ...args]);
}

function execCast(args) {
  return execFileSync(CAST_BIN, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
}

function parseJson(output) {
  const jsonStart = output.indexOf("{");
  if (jsonStart === -1) {
    throw new Error(`cast did not return JSON: ${output}`);
  }
  return JSON.parse(output.slice(jsonStart));
}

function bytes32(value) {
  return `0x${crypto.createHash("sha256").update(value).digest("hex")}`;
}

function tx(action, from, receipt) {
  return {
    action,
    from,
    transactionHash: receipt.transactionHash,
    gasUsed: Number.parseInt(String(receipt.gasUsed), 16),
    blockNumber: Number.parseInt(String(receipt.blockNumber), 16),
    status: receipt.status,
  };
}

function csv(transactions) {
  const rows = ["action,from,transactionHash,gasUsed,blockNumber,status"];
  for (const item of transactions) {
    rows.push(
      [
        item.action,
        item.from,
        item.transactionHash,
        item.gasUsed,
        item.blockNumber,
        item.status,
      ].join(","),
    );
  }
  return `${rows.join("\n")}\n`;
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
