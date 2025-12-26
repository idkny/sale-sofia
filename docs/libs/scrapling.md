# scrapling Documentation

Source: https://github.com/D4Vinci/Scrapling
Branch: main
Synced: 2025-12-26T14:03:43.378539

============================================================


## File: CODE_OF_CONDUCT.md
<!-- Source: CODE_OF_CONDUCT.md -->

# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or
  advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
karim.shoair@pm.me.
All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining
the consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction

**Community Impact**: Use of inappropriate language or other behavior deemed
unprofessional or unwelcome in the community.

**Consequence**: A private, written warning from community leaders, providing
clarity around the nature of the violation and an explanation of why the
behavior was inappropriate. A public apology may be requested.

### 2. Warning

**Community Impact**: A violation through a single incident or series
of actions.

**Consequence**: A warning with consequences for continued behavior. No
interaction with the people involved, including unsolicited interaction with
those enforcing the Code of Conduct, for a specified period of time. This
includes avoiding interactions in community spaces as well as external channels
like social media. Violating these terms may lead to a temporary or
permanent ban.

### 3. Temporary Ban

**Community Impact**: A serious violation of community standards, including
sustained inappropriate behavior.

**Consequence**: A temporary ban from any sort of interaction or public
communication with the community for a specified period of time. No public or
private interaction with the people involved, including unsolicited interaction
with those enforcing the Code of Conduct, is allowed during this period.
Violating these terms may lead to a permanent ban.

### 4. Permanent Ban

**Community Impact**: Demonstrating a pattern of violation of community
standards, including sustained inappropriate behavior,  harassment of an
individual, or aggression toward or disparagement of classes of individuals.

**Consequence**: A permanent ban from any sort of public interaction within
the community.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.0, available at
https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.

Community Impact Guidelines were inspired by [Mozilla's code of conduct
enforcement ladder](https://github.com/mozilla/diversity).

[homepage]: https://www.contributor-covenant.org

For answers to common questions about this code of conduct, see the FAQ at
https://www.contributor-covenant.org/faq. Translations are available at
https://www.contributor-covenant.org/translations.


----------------------------------------


## File: CONTRIBUTING.md
<!-- Source: CONTRIBUTING.md -->

# Contributing to Scrapling

Thank you for your interest in contributing to Scrapling! 

Everybody is invited and welcome to contribute to Scrapling. 

Minor changes have a better chance of being included promptly. Adding unit tests for new features or test cases for bugs you've fixed helps us ensure that the Pull Request (PR) is acceptable.

There are many ways to contribute to Scrapling. Here are some of them:

- Report bugs and request features using the [GitHub issues](https://github.com/D4Vinci/Scrapling/issues). Please follow the issue template to help us resolve your issue quickly.
- Blog about Scrapling. Tell the world how you’re using Scrapling. This will help newcomers with more examples and increase the Scrapling project's visibility.
- Join the [Discord community](https://discord.gg/EMgGbDceNQ) and share your ideas on how to improve Scrapling. We’re always open to suggestions.
- If you are not a developer, perhaps you would like to help with translating the [documentation](https://github.com/D4Vinci/Scrapling/tree/docs)?


## Finding work

If you have decided to make a contribution to Scrapling, but you do not know what to contribute, here are some ways to find pending work:

- Check out the [contribution](https://github.com/D4Vinci/Scrapling/contribute) GitHub page, which lists open issues tagged as good first issue. These issues provide a good starting point.
- There are also the [help wanted](https://github.com/D4Vinci/Scrapling/issues?q=is%3Aissue%20label%3A%22help%20wanted%22%20state%3Aopen) issues, but know that some may require familiarity with the Scrapling code base first. You can also target any other issue, provided it is not tagged as `invalid`, `wontfix`, or similar tags.
- If you enjoy writing automated tests, you can work on increasing our test coverage. Currently, the test coverage is around 90–92%.
- Join the [Discord community](https://discord.gg/EMgGbDceNQ) and ask questions in the `#help` channel.

## Coding style
Please follow these coding conventions as we do when writing code for Scrapling:
- We use [pre-commit](https://pre-commit.com/) to automatically address simple code issues before every commit, so please install it and run `pre-commit install` to set it up. This will install hooks to run [ruff](https://docs.astral.sh/ruff/), [bandit](https://github.com/PyCQA/bandit), and [vermin](https://github.com/netromdk/vermin) on every commit. We are currently using a workflow to automatically run these tools on every PR, so if your code doesn't pass these checks, the PR will be rejected.
- We use type hints for better code clarity and [pyright](https://github.com/microsoft/pyright) for static type checking, which depends on the type hints, of course.
- We use the conventional commit messages format as [here](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13#types), so for example, we use the following prefixes for commit messages:
   
   | Prefix      | When to use it           |
   |-------------|--------------------------|
   | `feat:`     | New feature added        |
   | `fix:`      | Bug fix                  |
   | `docs:`     | Documentation change/add |
   | `test:`     | Tests                    |
   | `refactor:` | Code refactoring         |
   | `chore:`    | Maintenance tasks        |
    
    Then include the details of the change in the body/description of the commit message.

   Example:
   ```
   feat: add `adaptive` for similar elements
   
   - Added find_similar() method
   - Implemented pattern matching
   - Added tests and documentation
   ```

> Please don’t put your name in the code you contribute; git provides enough metadata to identify the author of the code.

## Development
Setting the scrapling logging level to `debug` makes it easier to know what's happening in the background.
```python
import logging
logging.getLogger("scrapling").setLevel(logging.DEBUG)
```
Bonus: You can install the beta of the upcoming update from the dev branch as follows
```commandline
pip3 install git+https://github.com/D4Vinci/Scrapling.git@dev
```

## Building Documentation
Documentation is built using [MkDocs](https://www.mkdocs.org/). You can build it locally using the following commands:
```bash
pip install mkdocs-material
mkdocs serve  # Local preview
mkdocs build  # Build the static site
```

## Tests
Scrapling includes a comprehensive test suite that can be executed with pytest. However, first, you need to install all libraries and `pytest-plugins` listed in `tests/requirements.txt`. Then, running the tests will result in an output like this:
   ```bash
   $ pytest tests -n auto
   =============================== test session starts ===============================
   platform darwin -- Python 3.13.8, pytest-8.4.2, pluggy-1.6.0 -- /Users/<redacted>/.venv/bin/python3.13
   cachedir: .pytest_cache
   rootdir: /Users/<redacted>/scrapling
   configfile: pytest.ini
   plugins: asyncio-1.2.0, anyio-4.11.0, xdist-3.8.0, httpbin-2.1.0, cov-7.0.0
   asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
   10 workers [271 items]    
   scheduling tests via LoadScheduling 
   
   ...<shortened>...
   
   =============================== 271 passed in 52.68s ==============================
   ```
Hence, we used `-n auto` in the command above to run tests in threads to increase speed.

Bonus: You can also see the test coverage with the `pytest` plugin below
```bash
pytest --cov=scrapling tests/
```

## Making a Pull Request
To ensure that your PR gets accepted, please make sure that your PR is based on the latest changes from the dev branch and that it satisfies the following requirements:

- The PR should be made against the [**dev**](https://github.com/D4Vinci/Scrapling/tree/dev) branch of Scrapling. Any PR made against the main branch will be rejected.
- The code should be passing all available tests. We are using tox with GitHub's CI to run the current tests on all supported Python versions with every commit.
- The code should be passing all code quality checks we mentioned above. We are using GitHub's CI to enforce the code style checks performed by pre-commit. If you were using the pre-commit hooks we discussed above, you should not see any issues when committing your changes.
- Make your changes, keep the code clean with an explanation of any part that might be vague, and remember to create a separate virtual environment for this project.
- If you are adding a new feature, please add tests for it.
- If you are fixing a bug, please add code with the PR that reproduces the bug.

----------------------------------------


## File: ROADMAP.md
<!-- Source: ROADMAP.md -->

## TODOs
- [x] Add more tests and increase the code coverage.
- [x] Structure the tests folder in a better way.
- [x] Add more documentation.
- [x] Add the browsing ability.
- [x] Create detailed documentation for the 'readthedocs' website, preferably add GitHub action for deploying it.
- [ ] Create a Scrapy plugin/decorator to make it replace parsel in the response argument when needed.
- [x] Need to add more functionality to `AttributesHandler` and more navigation functions to `Selector` object (ex: functions similar to map, filter, and reduce functions but here pass it to the element and the function is executed on children, siblings, next elements, etc...)
- [x] Add `.filter` method to `Selectors` object and other similar methods.
- [ ] Add functionality to automatically detect pagination URLs
- [ ] Add the ability to auto-detect schemas in pages and manipulate them.
- [ ] Add `analyzer` ability that tries to learn about the page through meta-elements and return what it learned
- [ ] Add the ability to generate a regex from a group of elements (Like for all href attributes)
- 

----------------------------------------
