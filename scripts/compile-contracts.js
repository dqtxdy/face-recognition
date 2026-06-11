import fs from "node:fs";
import path from "node:path";
import solc from "solc";

const contractPath = path.join("contracts", "TrustFaceChain.sol");
const source = fs.readFileSync(contractPath, "utf8");

const input = {
  language: "Solidity",
  sources: {
    "TrustFaceChain.sol": {
      content: source,
    },
  },
  settings: {
    optimizer: {
      enabled: true,
      runs: 200,
    },
    outputSelection: {
      "*": {
        "*": ["abi", "evm.bytecode.object", "evm.deployedBytecode.object"],
      },
    },
  },
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));
const errors = output.errors ?? [];
const fatal = errors.filter((entry) => entry.severity === "error");

for (const entry of errors) {
  const prefix = entry.severity === "error" ? "ERROR" : "WARN";
  console.error(`${prefix}: ${entry.formattedMessage}`);
}

if (fatal.length > 0) {
  process.exit(1);
}

const compiled = output.contracts["TrustFaceChain.sol"].TrustFaceChain;
const buildDir = path.join("build", "contracts");
fs.mkdirSync(buildDir, { recursive: true });
fs.writeFileSync(
  path.join(buildDir, "TrustFaceChain.json"),
  JSON.stringify(
    {
      contractName: "TrustFaceChain",
      abi: compiled.abi,
      bytecode: `0x${compiled.evm.bytecode.object}`,
      deployedBytecode: `0x${compiled.evm.deployedBytecode.object}`,
    },
    null,
    2,
  ),
);

fs.writeFileSync(
  path.join("contracts", "TrustFaceChain.abi.json"),
  `${JSON.stringify(compiled.abi, null, 2)}\n`,
);

console.log("Compiled TrustFaceChain.sol");
console.log(`ABI entries: ${compiled.abi.length}`);
console.log(`Bytecode bytes: ${compiled.evm.bytecode.object.length / 2}`);

