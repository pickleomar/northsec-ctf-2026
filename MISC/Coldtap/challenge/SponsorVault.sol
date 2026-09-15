// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SponsorVault {
    bytes32 public constant DOMAIN_TYPEHASH =
        0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f;
    bytes32 public constant CHECKIN_TYPEHASH =
        0x385e35cb9f8fa1996d9da1c208387fe8508c0d6e7bb8d955c4c5550084f41da6;
    bytes32 public constant RELEASE_TYPEHASH =
        0xb29729e824b871332b6b0fe124be7dc59f40032f65c0f8cf77789599805a0069;
    bytes32 private constant DOMAIN_NAME_HASH =
        0x4d1cf9f8358a381d6cc7c23df6d7ebba5d7e44a27b27a5caf4484729aadcf1f7;
    bytes32 private constant DOMAIN_VERSION_HASH =
        0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6;

    address public immutable owner;
    bytes32 public immutable DOMAIN_SEPARATOR;
    bool public claimed;

    event Claimed(address indexed claimer);

    constructor(address _owner) {
        owner = _owner;
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                DOMAIN_TYPEHASH,
                DOMAIN_NAME_HASH,
                DOMAIN_VERSION_HASH,
                block.chainid,
                address(this)
            )
        );
    }

    function claim(bytes calldata signature) external {
        require(!claimed, "already claimed");

        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19\x01",
                DOMAIN_SEPARATOR,
                keccak256(abi.encode(RELEASE_TYPEHASH, msg.sender))
            )
        );

        (bytes32 r, bytes32 s, uint8 v) = _split(signature);
        require(ecrecover(digest, v, r, s) == owner, "bad release signature");

        claimed = true;
        emit Claimed(msg.sender);
    }

    function _split(
        bytes calldata signature
    ) private pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(signature.length == 65, "bad signature length");
        assembly {
            r := calldataload(signature.offset)
            s := calldataload(add(signature.offset, 0x20))
            v := byte(0, calldataload(add(signature.offset, 0x40)))
        }
    }
}
