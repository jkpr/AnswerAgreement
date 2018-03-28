# This module 'aa' stands for Answer Agreement.

The experiment is this:

* Each member of a group records the answers from a respondent.
* All members of all groups submit their surveys to form a dataset.

This dataset is analyzed with this module.

A dataset is all submissions for a survey. A column in the dataset
should identify which submitted surveys belong to which group. The
simplest way to do this is to have a `group_id` column.

Standard use cases for analysis are take as input a dataset and
possibly a start and end column. In that case, the following analyzes:

```
>>> DatasetAgreement.from_file(df_path, group_column, mask_first=first, mask_last=last)
```

Another standard use case is to analyze results from an ODK dataset.
Here, an XlsForm and a dataset are used as inputs, and possibly a start
and end column. The XlsForm helps to make a mask of meaningful columns
for comparison. Use the following:

```
>>> DatasetAgreement.from_csv_and_odk(csv_path, odk_path, group_column, mask_first=first, mask_last=last)
```

# Command-line interface

There is also a helpful command-line interface

```
$ python3 -m aa
