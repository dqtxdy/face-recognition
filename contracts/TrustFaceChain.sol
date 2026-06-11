// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract TrustFaceChain {
    struct IdentityRecord {
        bytes32 templateCommitment;
        bytes32 consentHash;
        bytes32 modelVersion;
        bool enrolled;
        bool revoked;
        uint256 enrolledAt;
        uint256 revokedAt;
    }

    address public immutable owner;
    mapping(bytes32 => IdentityRecord) private identities;

    event IdentityEnrolled(
        bytes32 indexed subjectId,
        bytes32 templateCommitment,
        bytes32 modelVersion,
        bytes32 consentHash
    );

    event VerificationLogged(
        bytes32 indexed subjectId,
        bytes32 verificationHash,
        bytes32 modelVersion,
        bool accepted
    );

    event TemplateRevoked(bytes32 indexed subjectId, bytes32 reasonHash);

    error AlreadyEnrolled(bytes32 subjectId);
    error NotEnrolled(bytes32 subjectId);
    error Revoked(bytes32 subjectId);
    error EmptyValue();

    constructor() {
        owner = msg.sender;
    }

    function enrollIdentity(
        bytes32 subjectId,
        bytes32 templateCommitment,
        bytes32 consentHash,
        bytes32 modelVersion
    ) external {
        if (subjectId == bytes32(0) || templateCommitment == bytes32(0)) {
            revert EmptyValue();
        }
        if (identities[subjectId].enrolled && !identities[subjectId].revoked) {
            revert AlreadyEnrolled(subjectId);
        }

        identities[subjectId] = IdentityRecord({
            templateCommitment: templateCommitment,
            consentHash: consentHash,
            modelVersion: modelVersion,
            enrolled: true,
            revoked: false,
            enrolledAt: block.timestamp,
            revokedAt: 0
        });

        emit IdentityEnrolled(
            subjectId,
            templateCommitment,
            modelVersion,
            consentHash
        );
    }

    function logVerification(
        bytes32 subjectId,
        bytes32 verificationHash,
        bytes32 modelVersion,
        bool accepted
    ) external {
        IdentityRecord memory record = identities[subjectId];
        if (!record.enrolled) {
            revert NotEnrolled(subjectId);
        }
        if (record.revoked) {
            revert Revoked(subjectId);
        }
        if (verificationHash == bytes32(0)) {
            revert EmptyValue();
        }

        emit VerificationLogged(
            subjectId,
            verificationHash,
            modelVersion,
            accepted
        );
    }

    function revokeTemplate(bytes32 subjectId, bytes32 reasonHash) external {
        IdentityRecord storage record = identities[subjectId];
        if (!record.enrolled) {
            revert NotEnrolled(subjectId);
        }
        if (record.revoked) {
            revert Revoked(subjectId);
        }

        record.revoked = true;
        record.revokedAt = block.timestamp;

        emit TemplateRevoked(subjectId, reasonHash);
    }

    function isRevoked(bytes32 subjectId) external view returns (bool) {
        return identities[subjectId].revoked;
    }

    function getIdentity(
        bytes32 subjectId
    ) external view returns (IdentityRecord memory) {
        return identities[subjectId];
    }
}

