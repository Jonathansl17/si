# si

Spring Initializr from the terminal. Run `si` in any folder and it asks for
every option the [start.spring.io](https://start.spring.io) form offers, then
creates the project right there.

Options are read live from the Initializr API, so new Spring Boot versions,
Java versions and dependencies show up without updating `si`.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/Jonathansl17/si/main/install.sh | sh
```

Requires `python3` (3.10+) and [`fzf`](https://github.com/junegunn/fzf) for
interactive mode. Running the installer again updates to the latest version.

## Usage

```sh
si                 # interactive: creates ./<artifact>
si --here          # interactive: generates into the current directory
```

It walks through Project, Language, Spring Boot, Group, Artifact, Name,
Description, Package name, Packaging, Configuration, Java and Dependencies.
Every prompt starts on the web form's default, so ENTER keeps it.

Dependencies are a fuzzy search: type `jpa`, press TAB to add it, type
`postgres`, TAB, and ENTER when done. Only dependencies compatible with the
chosen Spring Boot version are listed, and the bottom pane shows each one's
description.

### Non-interactive

Any option passed as a flag is not asked. `-y` skips every prompt and uses
defaults for the rest:

```sh
si -y -t maven-project -j 21 -c yaml -g com.acme -a orders \
   -d web,data-jpa,postgresql,lombok,validation
```

| Flag | Option |
| --- | --- |
| `-t, --type` | `maven-project`, `gradle-project`, `gradle-project-kotlin`, `maven-build`, `gradle-build` |
| `-l, --language` | `java`, `kotlin`, `groovy` |
| `-b, --boot` | Spring Boot version id |
| `-g, --group` / `-a, --artifact` | Maven coordinates |
| `-n, --name` / `--description` | Project name and description |
| `-p, --package` | Base package (defaults to group + artifact) |
| `--packaging` | `jar`, `war` |
| `-c, --config` | `properties`, `yaml` |
| `-j, --java` | Java version |
| `--project-version` | Project version |
| `-d, --deps` | Comma-separated dependency ids |
| `--list-deps` | Print dependency ids for the chosen Boot version |

`SI_SERVICE_URL` points `si` at a self-hosted Initializr.

## Development

```sh
python3 -m unittest discover -s tests -t .
```

## License

[MIT](LICENSE)
