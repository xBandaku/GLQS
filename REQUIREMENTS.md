# Set up GLQS for development

This guide assumes you are new to development and starting on Windows with
none of the required tools installed. You need an internet connection for the
downloads. Run commands one line at a time and wait for each to finish. If a
command fails, stop and resolve the error before continuing.

If you only want to play with GLQS, you do not need these development tools.
Follow the installation instructions in [README.md](README.md) instead.

## 1. Install the tools

Install these three free tools from their official websites:

| Tool | Version to choose | What GLQS uses it for |
| --- | --- | --- |
| [Python for Windows](https://www.python.org/downloads/windows/) | Python 3.13; an existing 3.12 installation also works | Running the build script and tests |
| [Node.js](https://nodejs.org/en/download) | Node.js 24.x with npm | Running the QSP compiler and engine tests |
| [Git for Windows](https://git-scm.com/install/windows) | Current stable Windows installer | Downloading GLQS and the reference game source |

For Python, choose a regular Windows installer for Python 3.13. Enable
**Add python.exe to PATH** on the first installer screen, then choose
**Install Now**. PATH is the list of folders Windows searches for commands.
The [Python Windows instructions](https://docs.python.org/3.13/using/windows.html#installation-steps)
describe these installer options.

For Node.js, select version **24.x**, **Windows**, and the **Windows Installer
(.msi)** download. Keep npm and the PATH option enabled in the installer.
The website may offer a newer major version by default; this project uses 24.
You do not need the optional tools for compiling native modules for GLQS.

For Git, use the Windows installer and keep the option that makes Git available
from the command line and other software. The other default options are fine.

Most Intel and AMD Windows computers use x64 installers. If Windows Settings
under System > About identifies an ARM-based processor, choose ARM64 installers.

After installing, close any open terminal windows. Open the Start menu, search
for **PowerShell**, and open it normally. You do not need to run it as
administrator for the commands below.

## 2. Check that the tools work

Copy each command into PowerShell and press Enter:

```powershell
python --version
node --version
npm.cmd --version
git --version
```

Each command should print a version: Python `3.13.x` or `3.12.x`, Node
`v24.x.x`, and version numbers for npm and Git. The `x` characters stand for
patch version numbers, so your output will contain digits instead.

This guide uses `npm.cmd`, the Windows npm command, so PowerShell does not need
permission to run the accompanying `npm.ps1` script.

If a command is not recognized, close and reopen PowerShell first. If it still
fails, revisit that tool's installer and its PATH option. If `python` opens the
Microsoft Store, make sure Python is installed and available on PATH before
continuing. If you see `>>>`, you opened Python's interactive prompt; type
`exit()` and return to PowerShell.

## 3. Download and open the project

If you already have the GLQS source folder, keep it and skip the download
commands. Otherwise, these commands download it into a folder called `GLQS`
inside your Windows user folder:

```powershell
Set-Location $env:USERPROFILE
git clone https://github.com/xBandaku/GLQS.git
Set-Location GLQS
```

If a `GLQS` folder already exists, do not delete or overwrite it to run this
step. Open the existing project folder instead.

To open an existing copy, use `Set-Location` with its actual path. For example,
if you saved the project in `D:\GLQS`, run:

```powershell
Set-Location 'D:\GLQS'
```

Check the folder contents:

```powershell
Get-ChildItem
```

You should see `build.py`, `src`, `tests`, and this `REQUIREMENTS.md` file.
This folder is the **repository root**. Run all remaining commands from here.

## 4. Install the project packages

```powershell
npm.cmd ci --prefix build/tooling --include=dev --no-audit --no-fund
```

This downloads the compiler and runtime test tools into
`build/tooling/node_modules` inside the project. `ci` installs the versions
recorded in `build/tooling/package-lock.json`. `--include=dev` ensures the
required tools are installed even if npm is configured to omit development
packages. No global npm installation is needed.

The direct packages are `@qsp/cli`, `@qsp/converters`, and `@qsp/wasm-engine`.
Their pinned versions are in `build/tooling/package.json`. Python uses only its
standard library, so there are no pip packages to install.

Wait for the command to finish successfully. A warning is different from an
installation error; if npm reports an error, resolve it before continuing.

## 5. Download the game source used by the tests

GLQS checks some of its behavior against Girl Life's actual source code. These
commands download a fixed snapshot into `reference/nightly`. They do not
install Girl Life or change an installed game.

Only run these three commands when setting up a new reference folder:

```powershell
git init reference/nightly
git -C reference/nightly fetch --depth 1 https://gitlab.com/kevinsmartstfg/girl-life.git 83b164f64224f1ba88fd409469c1a9379ad34f86
git -C reference/nightly checkout --detach FETCH_HEAD
```

The first command creates a separate Git repository in that folder. The second
downloads the specified commit with minimal history. The third puts that
commit's files into the folder without following a branch.

Despite its name, `nightly` does not automatically update. Keep these files
unchanged so the checks use the expected snapshot.

If `reference/nightly` already exists, preserve it and check its commit instead:

```powershell
git -C reference/nightly rev-parse HEAD
```

The output must be `83b164f64224f1ba88fd409469c1a9379ad34f86`.
If it differs or the command fails, stop and ask the project maintainer before
replacing an existing checkout.

## 6. Run the tests

```powershell
python -m unittest discover -s tests -v
```

A complete successful run ends with `OK` and has no skipped tests. `FAILED`
or `ERROR` means a check failed. `OK (skipped=...)` means some checks did not
run, often because the reference source or runtime packages are missing.
Read the skip reason and complete the corresponding setup step.

These tests include static build checks and isolated QSP engine tests. They
do not replace trying the mod in the full game.

## 7. Build the mod

```powershell
$env:PATH = (Resolve-Path 'build/tooling/node_modules/.bin').Path + ';' + $env:PATH
python build.py
```

The first line lets this PowerShell window find the locally installed compiler.
Run it again when building in a new PowerShell window. It does not permanently
change your Windows PATH.

The build should end with `SUCCESS:` followed by the path to `build/GLQS.qsp`.
That file is the compiled mod. Follow [README.md](README.md) to install it into
a compatible Girl Life game and test it in a QSP player. Building does not
automatically copy it into the game.

Edit gameplay source in `src/*.qsps`. The assembled `build/GLQS.qsps` and
compiled `build/GLQS.qsp` are generated files and will be replaced by builds.

## Returning to the project later

Open PowerShell, navigate to the project folder, run the tests, then run both
commands in step 7. You normally install the tools and download the reference
only once. Rerun step 4 when the package manifest or lockfile changes, or when
the installed project packages are missing.

## Linux and macOS

The numbered walkthrough above is for Windows. On Linux or macOS, install
Python 3.12 or 3.13, Node.js 24 with npm, and Git using the appropriate
installers for your system. Use `cd` to enter the repository, `npm` instead of
`npm.cmd`, and `python3` instead of `python`. The reference Git commands are
the same. Before building, set the compiler path in your shell with:

```sh
export PATH="$PWD/build/tooling/node_modules/.bin:$PATH"
python3 build.py
```
