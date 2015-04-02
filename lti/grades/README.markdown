# LTI Grading

Upload grades from a CSV to an LTI unit.

## Course Configuration
- Add the following to `Advanced Settings`
    - Advanced Module List
        - `[ "lti" ]`
    - LTI Passport
        - `[ "MY_LTI_ID:MY_LTI_KEY:MY_LTI_SECRET" ]`
- Add an LTI component to course
- Edit the component:
    - `Hide External Tool`: `True`
    - `LTI ID`: `MY_LTI_ID`
    - `Scored`: `True`

## Generate Grade CSV
- Go to `Instructor Dashboard`.
- Go to `Data Download` tab.
- Click `Download profile information as a CSV`.
- Open file in `Numbers` (if using Excel, see below for instructions to
  remove the `^M` characters it adds).
- Make column headings agree with what the grade_csv argument (above)
  expects: ID / email / grade / max_grade / comments
- Put in student grades, max grades, and comments.
- Export as CSV.

## Get Anonymous IDs CSV
- Go to `Instructor Dashboard`.
- Go to `Data Download` tab.
- Click `Get Student Anonymized IDs CSV`.

## Installation
From a terminal window:
- `mkvirtualenv lti`
- `workon lti`
- `pip install -r requirements.txt`

## Usage
From a terminal window:
- `workon lti`
- `./upload_csv.py --help`
- `./upload_csv.py --platform-url https://YOUR_LMS_PLATFORM_URL_HERE COURSE_ID_HERE path/to/edited/profile.csv path/to/downloaded/anonymous_ids.csv MY_LTI_KEY MY_LTI_SECRET`

## Trust, but verify
Check terminal readout and make sure all there are no BAD ROWs (except
possibly the first one, where your headings were).
- Note: You can’t input a grade higher than the max grade.

## Clean up of CSV file (optional)
- Double-check CSV address for `^M`
- In terminal, type `vim <filename.ext>` (ex: `vim - Week9_Group1.uniq.csv`).
    - Type `:` to start the command.
    - Find and replace `^M` with nothing in `vim`:
        - Type `%s/^M/\r/g` (for `^M` press `CONTROL + v` and then `CONTROL + m`)
    - Hit `escape`
    - Type `:wq` to save and exit (w = write/save, q = quit).
