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

## Local Simulator

Until Hardhat or Foundry is installed, the Python simulator mirrors the contract
state transitions:

```bash
make chain-demo
```

This demonstrates:

1. enrollment event,
2. verification event,
3. revocation event,
4. verification blocked after revocation.

## Deployment Options

### Fast classroom route

Use Remix:

1. Open https://remix.ethereum.org.
2. Create `TrustFaceChain.sol`.
3. Paste the contract code.
4. Compile with Solidity `0.8.24` or compatible.
5. Deploy to the Remix VM for presentation.

### Engineering route

Use Hardhat or Foundry later for:

- local EVM deployment,
- Solidity unit tests,
- gas reports,
- app integration through JSON-RPC.

The current ABI is included so the app can be wired before a compiler is added.

