# kiro-community-repo
Community-maintained package repository for Kiro IDE on Linux.

This project provides signed APT repository metadata while package binaries are downloaded directly from the official Kiro distribution servers.

> ⚠️ Unofficial project
>
> [!IMPORTANT]
> This is an unofficial community project. It is not affiliated with, endorsed by, or supported by Amazon Web Services or the Kiro team.
> Project status: Experimental

## Why this repository exists

Kiro provides Debian packages for Linux, but it does not currently provide a native APT repository.

Without an APT repository, Linux users must manually download and install every new `.deb` release.

This project provides the standard Debian package management experience:

```bash
sudo apt update
sudo apt install kiro
sudo apt upgrade
```

## How it works

The repository uses the following architecture:

```text
Official Kiro metadata
        |
        v
GitHub Actions
        |
        | Downloads the latest official .deb temporarily
        | Reads the Debian package metadata
        | Generates Packages and Release files
        | Signs the repository metadata
        v
GitHub Pages
        |
        | Serves signed APT metadata
        v
Cloudflare Worker
        |
        | Redirects package download requests
        v
Official Kiro distribution servers
```

GitHub Pages hosts only the repository metadata:

- `Packages`
- `Packages.gz`
- `Release`
- `InRelease`
- `Release.gpg`
- the public repository signing key

Kiro package binaries are not stored or redistributed by this repository.

When APT requests a package under `/pool/`, the Cloudflare Worker redirects the request to the corresponding official Kiro download URL.

## Supported platforms

The repository currently supports:

- Debian-based Linux distributions
- `amd64` / `x86_64`
- Kiro stable releases

Additional architectures or package formats may be added in the future.

## Installation

Replace `https://kiro-community-worker.giovannimet.workers.dev` below with the repository domain once the Cloudflare Worker has been deployed.

### 1. Install the repository signing key

```bash
curl -fsSL https://kiro-community-worker.giovannimet.workers.dev/public/pubkey.asc \
  | sudo gpg --dearmor \
  --yes \
  --output /usr/share/keyrings/kiro-community.gpg
```

Verify that the keyring was created:

```bash
gpg \
  --no-default-keyring \
  --keyring /usr/share/keyrings/kiro-community.gpg \
  --fingerprint
```

The expected fingerprint is:

```text
D72C A808 5EAF A331 EBE0 ED84 9373 7AFF 88AE 4ACE
```

### 2. Add the repository

```bash
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/kiro-community.gpg] https://kiro-community-worker.giovannimet.workers.dev stable main" \
  | sudo tee /etc/apt/sources.list.d/kiro-community.list
```

### 3. Update the APT package index

```bash
sudo apt update
```

### 4. Install Kiro

```bash
sudo apt install kiro
```

## Updating Kiro

Once the repository has been configured, Kiro can be updated using the standard APT workflow:

```bash
sudo apt update
sudo apt upgrade
```

To update only Kiro:

```bash
sudo apt update
sudo apt install --only-upgrade kiro
```

## Repository signing key

Repository metadata is signed with the following key:

```text
UID:
Kiro Community Repository
(Kiro Community Package Repository)
<GiovanniMet@users.noreply.github.com>

Fingerprint:
D72C A808 5EAF A331 EBE0 ED84
9373 7AFF 88AE 4ACE

Long key ID:
93737AFF88AE4ACE
```

The ASCII-armored public key is available at:

```text
/public/pubkey.asc
```

A copy is also published in the repository root as:

```text
/KEYS
```

The fingerprint should always be verified before trusting the repository.

## Security model

The trust chain is:

```text
Repository signing key
        |
        | Signs Release and InRelease
        v
APT repository metadata
        |
        | Contains the expected package size and checksums
        v
Official Kiro package
        |
        | Downloaded from official Kiro infrastructure
        v
APT verifies the downloaded package against the signed metadata
```

The GitHub Actions workflow temporarily downloads the official Kiro Debian package to:

1. inspect its package metadata;
2. obtain the Debian package name, version, architecture and dependencies;
3. calculate its size and cryptographic checksums;
4. generate the APT repository indexes.

The downloaded `.deb` is not committed to Git, uploaded to GitHub Pages, or redistributed by this project.

The generated metadata preserves the complete Debian package version. For example:

```text
Upstream release: 1.4.13
Debian package:   1.4.13-1792541582
```

The Debian package itself is treated as the authoritative source for the package version included in the APT index.

## Automated updates

A scheduled GitHub Actions workflow checks the official Kiro release metadata every 6 hours.
If the latest version matches `state/latest.json`, the workflow skips the package
download, repository build, and deployment.

When a release is detected, the workflow:

1. discovers the latest stable Kiro version;
2. downloads the official Debian package temporarily;
3. extracts the package metadata using Debian tooling;
4. generates `Packages` and `Packages.gz`;
5. generates the repository `Release` file;
6. signs the metadata as `InRelease` and `Release.gpg`;
7. verifies the generated signatures;
8. checks that no `.deb` file is tracked by Git;
9. commits the updated metadata;
10. deploys the metadata to GitHub Pages.

The workflow can also be started manually from the GitHub Actions interface.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── update.yml
├── dists/
│   └── stable/
│       ├── InRelease
│       ├── Release
│       ├── Release.gpg
│       └── main/
│           └── binary-amd64/
│               ├── Packages
│               └── Packages.gz
├── public/
│   └── pubkey.asc
├── scripts/
│   ├── build_pages.sh
│   ├── fetch_kiro.py
│   └── generate_repo.sh
├── state/
│   └── latest.json
├── KEYS
├── LICENSE
└── README.md
```

The `pool/` directory is intentionally not published by GitHub Pages.

Package requests under `/pool/` are handled by the redirect layer and forwarded to official Kiro distribution infrastructure.

## Verifying repository metadata manually

Download the repository public key:

```bash
curl -fsSLO https://kiro-community-worker.giovannimet.workers.dev/public/pubkey.asc
```

Download the signed repository metadata:

```bash
curl -fsSLO https://kiro-community-worker.giovannimet.workers.dev/dists/stable/InRelease
```

Import the public key into a temporary GPG home:

```bash
GNUPGHOME="$(mktemp -d)"
export GNUPGHOME

gpg --import pubkey.asc
```

Verify the signed metadata:

```bash
gpg --verify InRelease
```

The output should report a good signature from:

```text
Kiro Community Repository
(Kiro Community Package Repository)
<GiovanniMet@users.noreply.github.com>
```

Always compare the displayed fingerprint with:

```text
D72C A808 5EAF A331 EBE0 ED84
9373 7AFF 88AE 4ACE
```

Remove the temporary GPG home afterwards:

```bash
rm -rf "$GNUPGHOME"
unset GNUPGHOME
```

## Inspecting the published package metadata

The uncompressed package index is available at:

```text
/dists/stable/main/binary-amd64/Packages
```

It can be inspected with:

```bash
curl -fsSL \
  https://kiro-community-worker.giovannimet.workers.dev/dists/stable/main/binary-amd64/Packages
```

The entry should contain fields including:

```text
Package: kiro
Version: <complete Debian package version>
Architecture: amd64
Filename: pool/main/k/kiro/<official package filename>
Size: <package size>
SHA256: <package checksum>
```

## Removing the repository

Remove the repository definition:

```bash
sudo rm -f /etc/apt/sources.list.d/kiro-community.list
```

Remove the repository signing key:

```bash
sudo rm -f /usr/share/keyrings/kiro-community.gpg
```

Refresh the local package index:

```bash
sudo apt update
```

This does not uninstall Kiro.

To uninstall Kiro as well:

```bash
sudo apt remove kiro
```

## Troubleshooting

### Repository signature verification fails

Reinstall the repository public key:

```bash
curl -fsSL https://kiro-community-worker.giovannimet.workers.dev/public/pubkey.asc \
  | sudo gpg --dearmor \
  --yes \
  --output /usr/share/keyrings/kiro-community.gpg
```

Then verify the fingerprint:

```bash
gpg \
  --no-default-keyring \
  --keyring /usr/share/keyrings/kiro-community.gpg \
  --fingerprint
```

Expected fingerprint:

```text
D72C A808 5EAF A331 EBE0 ED84
9373 7AFF 88AE 4ACE
```

### APT cannot find the `kiro` package

Refresh the package index:

```bash
sudo apt update
```

Check that the repository is configured:

```bash
cat /etc/apt/sources.list.d/kiro-community.list
```

Inspect APT policy information:

```bash
apt-cache policy kiro
```

### Package download returns HTTP 404

The repository metadata may be available while the redirect layer is not correctly configured.

Verify that requests under:

```text
/pool/main/k/kiro/
```

are handled and redirected to the official Kiro distribution URL.

### Inspect package download behavior

APT download activity can be inspected with:

```bash
sudo apt-get \
  -o Debug::Acquire::https=true \
  install kiro
```

This is useful for confirming whether the `/pool/` request is being redirected correctly.

## Reporting issues

Before opening an issue, include:

- Linux distribution and version;
- system architecture;
- output of `apt-cache policy kiro`;
- relevant output from `sudo apt update`;
- the repository metadata version;
- the requested package URL, excluding any sensitive proxy or authentication information.

Do not include private keys, GitHub secrets, passphrases, access tokens, or other credentials.

## Contributing

Contributions are welcome.

Useful areas include:

- repository automation;
- metadata validation;
- documentation;
- additional Linux architectures;
- RPM or other package repository formats;
- automated repository testing;
- Cloudflare Worker validation;
- security and integrity checks.

Changes should preserve the core project principles:

1. package binaries remain hosted by the official Kiro infrastructure;
2. this repository publishes metadata only;
3. repository metadata is cryptographically signed;
4. package size and checksums are derived from the official package;
5. no private signing material is committed to Git;
6. the project must not imply affiliation with AWS or the Kiro team.

## Disclaimer

Kiro is a product and trademark of Amazon Web Services.

This project is independently maintained by the community and is not affiliated with, endorsed by, sponsored by, or supported by Amazon Web Services or the Kiro team.

All Kiro package binaries remain hosted on official Kiro distribution infrastructure.

Users are responsible for reviewing the applicable Kiro and AWS terms before downloading or using Kiro.

## License

The scripts, workflows and original repository content are provided under the license included in this repository.

The Kiro software packages referenced by this repository are distributed separately by Amazon Web Services and remain subject to their respective terms and licenses.
