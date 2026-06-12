# Smart Contract Layer

`TrustFaceChain.sol` is the on-chain accountability layer for the capstone.

It stores:

- subject id commitment,
- template commitment,
- consent hash,
- model version,
- revocation state,
- verification audit events.

It does not store:

- raw face images,
- aligned face crops,
- plain embeddings,
- decryption keys,
- personal names.

## Current Contract

- [TrustFaceChain.sol](TrustFaceChain.sol)
- [TrustFaceChain.abi.json](TrustFaceChain.abi.json)

The contract now uses an owner/operator model. The deployer is the owner, the
owner can approve operators, and only the owner or approved operators can
enroll identities, log verifications, or revoke templates.

## Local Simulator

The Python simulator mirrors the contract state transitions:

```bash
make chain-demo
```

This demonstrates:

1. enrollment event,
2. verification event,
3. revocation event,
4. verification blocked after revocation.

## Deployment Options

### Local Anvil route

Start Anvil:

```bash
/home/respectthanh/.foundry/bin/anvil --host 0.0.0.0 --port 8545
```

Then run:

```bash
make chain-live
```

Outputs:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`

The script deploys the contract, approves an operator, proves an unauthorized
write is rejected, runs enroll/verify/revoke, and records gas usage.

### Fast classroom route

Use Remix:

1. Open https://remix.ethereum.org.
2. Create `TrustFaceChain.sol`.
3. Paste the contract code.
4. Compile with Solidity `0.8.24` or compatible.
5. Deploy to the Remix VM for presentation.

### Engineering route

Use Hardhat or Foundry later for:

- Solidity unit tests,
- app integration through JSON-RPC.

The current ABI is included so the app can be wired before a compiler is added.
