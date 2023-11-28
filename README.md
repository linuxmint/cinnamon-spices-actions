# cinnamon-spices-actions

![Validate Spices](https://github.com/linuxmint/cinnamon-spices-actions/workflows/Validate%20Spices/badge.svg)

This repository hosts all the Actions available for the Cinnamon desktop environment.

Users can install Spices from the [Cinnamon Spices website](https://cinnamon-spices.linuxmint.com/), or directly from within Cinnamon -> System Settings.

## Definitions

### UUID

Each Spice is given a name which uniquely identifies them.

That name is their UUID and it is unique.

### Author

Each Spice has an author.

The GitHub username of the author is specified in the Spice's info.json file.

## File Structure

A Spice can contain many files, but it should have the following file structure:

- UUID/
- UUID/CHANGELOG.md
- UUID/README.md
- UUID/UUID.nemo_action.in
- UUID/info.json
- UUID/files/
- UUID/files/UUID
- UUID/files/UUID/icon.png
- UUID/files/UUID/metadata.json
- UUID/files/UUID/po/
- UUID/files/UUID/po/UUID.pot

There are two important directories:

- UUID/ is the root level directory, it includes files which are used by the website and on GitHub.
- UUID/files/ represents the content of the ZIP archive which users can download from the [Cinnamon Spices website](https://cinnamon-spices.linuxmint.com/) or which is sent to Cinnamon when installing the Spice from System Settings. This is the content which is interpreted by Cinnamon itself.

As you can see, the content of the Spice isn't placed inside UUID/files/ directly, but inside UUID/files/UUID/ instead. This guarantees files aren't extracted directly onto the file system, but placed in the proper UUID directory. The presence of this UUID directory, inside of files/ isn't actually needed by Cinnamon (as Cinnamon creates it if it's missing), but it is needed to guarantee a proper manual installation (i.e. when users download the ZIP from the Cinnamon Spices website).

Important notes:

- The UUID/UUID.nemo_action.in file is in the top-level directory, unlike other Spices. The translated .nemo_action file is computed when the ZIP file is generated for the Cinnamon Spices website.

- The UUID/files/ directory has to be "empty", which means that it should contain ONLY the UUID directory. Otherwise, the Spice wouldn't be installable through System Settings.

At the root level:

- CHANGELOG.md is optional and can be used to show information about changes made to the Spice. It also appears on the website.
- README.md is optional and can be used to show instructions and information about the Spice. It appears both in GitHub and on the website.
- UUID.nemo_action.in is the raw Action file without translations. It should contain `_Name`, `_Comment`, and `Exec` fields as a minimum. ([A sample Action file](https://github.com/linuxmint/nemo/blob/master/files/usr/share/nemo/actions/sample.nemo_action)) **(NOTE: The raw Action file has underscores on the Name and Comment keys. This is to facilitate translations of those fields.)**
- info.json contains information about the Spice. For instance, this is the file which contains the GitHub username of the Spice's author.

## Validation

To check if a Spice with UUID satisfies those requirements run the `validate-spice` script in this repo:

```bash
./validate-spice UUID
```

## Development

To facilitate easier testing of Actions locally, run the `test-spice` script in this repo:

Validate and then copy a Spice with UUID:

```bash
./test-spice UUID
```

Skip validation (not recommended) and then copy a Spice with UUID:

```bash
./test-spice -s UUID
```

Remove all locally installed development copies of Spices:

```bash
./test-spice -r
```

NOTE: Local copies of Spices for development/testing purposes will have a `devtest-` prefix attached for easier identification and cleanup.

## Rights and Responsibility of the Author

The author is in charge of the development of the Spice.

Authors can modify their Spice under the following conditions:

- They need to respect the file structure and workflow defined here
- They cannot introduce malicious code or code which would have a negative impact on the environment

Authors are able to accept or refuse changes from other people which modify the features or the look of their Spice.

Authors may choose to pass on development of their Action to someone else. In that case, the "author" field in UUID/info.json will be changed to the new developer and the "original_author" field will be added to give credit to the original developer.

If an author abandons their Action, the Linux Mint team will take over maintenance of the Action or pass it on to someone else. Several factors are used to determine if an Action is abandoned, including prolonged activity, failure to respond to requests, and serious breakages that have occurred due to changes in API, etc. If you plan to abandon an Action, please notify us, so we don't have to guess as to whether it is abandoned or not.

## Pull Requests From Authors and Workflow

To modify a Spice, developers create a pull request (PR).

Members of the cinnamon-spices-developers Team review the pull request.

If the author of the pull request is the Spice author (the GitHub username matches the author field in UUID/info.json), the reviewer only has to perform the following checks:

- The changes only impact Spices which belong to that author
- The changes respect the Spices file structure
- The changes do not introduce malicious code or code which would negatively impact the desktop environment

If everything is fine, the PR is merged, the website is updated and users can see a Spice update in System Settings.

## Pull Requests From Other People

In addition to the checks specified above, if the pull request comes from somebody other than the author, it will be held until the author reviews it or gives a thumbs-up, with the following exceptions:

- If it is a bug fix, the PR may be merged, though if the bug is minor, or the fix could potentially impact the way the Action works, we may wait for author approval before merging.
- If the pull request adds translations it will likewise be merged. These are not going to effect the functionality of the code, and will make the Action available to many users who couldn't use it before due to a language barrier. We view this as essentially a bug fix, but it is included here for clarification.
- If the author fails to respond in a reasonable time, we will assume the Action is abandoned (as mentioned above) and the pull request will be merged assuming it meets all other requirements.

If the changes represent a change in functionality, or in look and feel, or if their implementation could be questioned and/or discussed, the reviewer should leave the PR open and ask the author to review it.

If the author is happy with the PR, it can then be merged. If not, it can either be closed or updated to reflect any changes the author requested, at which point it will either be merged or the author may be asked to re-review the changes, depending on whether it is clear the changes fully meet the author's requirements.

## Deletions

Authors are entitled to remove their Spice.

The Cinnamon Team is also entitled to do so. Common reasons are lack of maintenance, critical bugs, or if the features are already provided, either by Cinnamon itself, or by another Spice which is more successful.

## Additions

New Spices can be added by pull request.

The Cinnamon Team can accept or reject the addition and should give justification in the PR comments section.

## Reporting Bugs and Creating Pull Requests

See the [Guidelines for Contributing](https://github.com/linuxmint/cinnamon-spices-actions/blob/master/.github/CONTRIBUTING.md).

## Translations

The script `cinnamon-spices-makepot` in this repo was written to help authors to create/update their translation template (`.pot`) file and to help translators to test their translations.

Creating or updating a translation template `.pot`:

```bash
./cinnamon-spices-makepot UUID
```

Test your translation's `.po` locally before uploading to Spices:

```bash
./cinnamon-spices-makepot UUID --install
```

## Translations Status Tables

The Spices receive updates which sometimes contain new or updated strings that need to be translated. The translation status tables were created to give translators a better overview of the current state of translations and also to make it easier to track where new untranslated strings appear.

- [Translation Status Tables for Actions](https://github.com/linuxmint/cinnamon-spices-actions/blob/translation-status-tables/.translation-tables/tables/README.md)

To ensure that these tables are always up-to-date, they are automatically regenerated whenever a new commit is pushed to the master branch.

## Action Sample

There is a [sample Action](https://github.com/linuxmint/nemo/blob/master/files/usr/share/nemo/actions/sample.nemo_action) file with examples and options available.
