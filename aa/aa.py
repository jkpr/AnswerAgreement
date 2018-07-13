#!/usr/bin/env python3
"""A module for analyzing answer agreement.

The experiment is this:

* Each member of a group records the answers from a respondent.
* All members of all groups submit their surveys to form a dataset.

This dataset is analyzed with this module.

A dataset is all submissions for a survey. A column in the dataset
should identify which submitted surveys belong to which group. The
simplest way to do this is to have a `group_id` column.

Standard use cases for analysis are take as input a dataset and
possibly a start and end column. In that case, the following analyzes:

>>> DatasetAgreement.from_file(df_path, group_column, mask_first=first,
...                            mask_last=last)

Another standard use case is to analyze results from an ODK dataset.
Here, an XlsForm and a dataset are used as inputs, and possibly a start
and end column. The XlsForm helps to make a mask of meaningful columns
for comparison. Use the following:

>>> DatasetAgreement.from_csv_and_odk(csv_path, odk_path, group_column,
...                                   mask_first=first, mask_last=last)

Logger:
    Has the name of 'aa.aa'

Dataset columns:
    C_CORRECT_ANSWER = 'correct_answer'
    C_ALL_MISSING = 'all_missing'
    C_GROUP_ALL_CORRECT = 'group_all_correct'
    C_CORRECT_ANSWER_COUNT = 'correct_answer_count'
    C_PERCENT_CORRECT = 'percent_correct'

Module attributes:
    SKIPPED_ODK_TYPES: A sequence of blacklisted ODK types that are not
        used for comparison within groups.
    SKIPPED_ODK_TYPES_START: A sequence of strings that blacklist all
        ODK types that begin with one of them.

This module's mascot is aa, the Hawaiian name for a frothy lava flow.
"""
from collections import namedtuple
from typing import Iterable, List

import pandas as pd
import xlrd


C_CORRECT_ANSWER = 'correct_answer'
C_ALL_MISSING = 'all_missing'
C_GROUP_ALL_CORRECT = 'group_all_correct'
C_CORRECT_ANSWER_COUNT = 'correct_answer_count'
C_PERCENT_CORRECT = 'percent_correct'


class GroupAgreement:
    """Class to hold analysis information for a group within a dataset.

    All results are attributes of the object.

    Instance attributes:
        dataframe: The full dataframe for this group
        group_id: The group id for this group
        column_mask: A list of column labels for which columns to keep
            and do analysis on. Default of None means to use all
            columns.
        group_size: The number of group members in this group.
        agreement_results: A dataframe with the column_mask as index and
            various calculated values of interest as columns.
        total_agreement: The proportion of masked questions with
            agreement.
        comparisons: The number of columns of comparison

    Properties:
        masked_dataframe: Group dataframe with the column mask applied.
        disagree_dataframe: Dataframe with only the columns where there
            is disagreement.
    """

    def __init__(self, dataframe: pd.DataFrame, group_id,
                 column_mask: list = None):
        """Initialize a GroupAgreement and do all relevant analysis.

        Args:
            dataframe: The full dataframe for this group.
            group_id: The group id for this group. Could be any value
                stored in a dataframe.
            column_mask: A list of column labels for which columns to
                keep and do analysis on. Default of None means to use
                all columns.
        """
        self.dataframe = dataframe
        self.group_id = group_id
        self.column_mask = column_mask
        self.group_size = len(self.dataframe)
        masked = self.masked_dataframe
        self.agreement_results = self.generate_agreement_measures(masked)
        completed_mask = ~self.agreement_results[C_ALL_MISSING]
        self.total_agreement = self.agreement_results.loc[
            completed_mask, C_GROUP_ALL_CORRECT
        ].mean()
        self.comparisons = completed_mask.sum()

    @staticmethod
    def generate_agreement_measures(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply analysis function to columns, combine results, return.

        The input dataframe is a standard dataset with measurement
        variables as column headers and records as individual surveys.
        This function creates a dataframe where the measurement
        variables form the index and the new column headers are the
        various computed quantities.

        Args:
            dataframe: The full dataframe for this group.

        Returns:
            A dataframe with the computed quantities of interest.
        """
        result = dataframe.T.apply(GroupAgreement.analyze_answer_votes, axis=1)
        return result

    @staticmethod
    def analyze_answer_votes(series: pd.Series) -> pd.Series:
        """Analyze a column of the dataset for agreement.

        This function is the workhorse of the analysis. It calculates
        all relevant quantities and saves them as a common series.

        This function calculates:

        * What the "correct" answer is based on the number of votes
        * Whether all values are missing
        * Whether each group member answered the same way
        * The number of group members answering the "correct" answer
        * The percentage of group members answering the "correct"
            answer

        Args:
            series: The column of the dataset to analyze.

        Returns:
            A series with calculated values and identifying names.
        """
        correct_answer = None
        all_missing = True
        group_all_correct = False
        correct_answer_count = 0

        group_size = len(series)
        counts = series.value_counts()
        if counts.empty:
            # All answers are NA, do nothing
            pass
        elif len(counts) == 1:
            # All are non-NA (at least one) are one answer
            correct_answer = counts.index[0]
            all_missing = False
            group_all_correct = counts.iloc[0] == group_size
            correct_answer_count = counts.iloc[0]
        elif counts.iloc[0] == counts.iloc[1]:
            # Top two answers have same vote count
            all_missing = False
        else:
            # One answer has more than anything else
            correct_answer = counts.index[0]
            all_missing = False
            correct_answer_count = counts.iloc[0]
        percent_correct = correct_answer_count / group_size
        new_series = pd.Series((
            correct_answer,
            all_missing,
            group_all_correct,
            correct_answer_count,
            percent_correct
        ), index=(
            C_CORRECT_ANSWER,
            C_ALL_MISSING,
            C_GROUP_ALL_CORRECT,
            C_CORRECT_ANSWER_COUNT,
            C_PERCENT_CORRECT,
        ))
        return new_series

    @property
    def masked_dataframe(self) -> pd.DataFrame:
        """Return the masked dataframe.

        Combines the full dataframe and the mask to create a masked
        dataframe.
        """
        masked_dataframe = self.dataframe
        if self.column_mask is not None:
            masked_dataframe = self.dataframe[self.column_mask]
        return masked_dataframe

    @property
    def disagree_dataframe(self) -> pd.DataFrame:
        """Return the dataframe of questions with disagreement.

        Returns:
            The subset of rows of the masked dataframe where there is
            disagreement and at least one answer.
        """
        completed_mask = ~self.agreement_results[C_ALL_MISSING]
        some_disagreement = ~self.agreement_results[C_GROUP_ALL_CORRECT]
        masked = self.masked_dataframe
        return masked.loc[:, completed_mask & some_disagreement]

    def print_summary(self):
        """Print a summary of results."""
        print(f'*** Summary for group {repr(self.group_id)}')
        print(f'- Points of comparison: {self.comparisons}')
        print(f'- Total agreement: {self.total_agreement}')

    def __repr__(self):
        """Get a representation of this object."""
        return f'<GroupAgreement {repr(self.group_id)}>'


class DatasetAgreement:
    """Class to hold answer agreement information for a whole dataset.

    Access to the individual GroupAgreement objects is meant through
    the `group` method.

    Instance attributes:
        dataframe: The full dataframe for the full dataset (has all
            groups).
        group_column: The column label for the column that defines
            which rows are in which groups. Default of None means the
            entire dataset is from the same group.
        column_mask: A list of column labels for which columns to keep
            and do analysis on. Default of None means to use all
            columns.
        unaccounted: A dataframe containing the rows that do not fit
            into any of the GroupAgreement objects. These are the rows
            that are null in a specified group_column.
        _data: A list of GroupAgreement objects, one for each group.

    Properties:
        group_ids: A list of the IDs in this dataset.
    """

    def __init__(self, dataframe: pd.DataFrame, group_column: str = None,
                 column_mask: list = None):
        """Analyze the groups of a dataframe.

        For each group in the dataset, this __init__ creates a
        GroupAgreement object and saves it.

        This __init__ uses a Pandas dataframe as input.

        The unaccounted attribute is populated only when a group_column
        is specified.

        Args:
            dataframe: The full dataframe for the full dataset (has
                all groups).
            group_column: The column label for the column that defines
                which rows are in which groups. Default of None means
                the entire dataset is from the same group.
            column_mask: A list of column labels for which columns to
                keep and do analysis on. Default of None means to use
                all columns.
        """
        self.dataframe = dataframe
        self.group_column = group_column
        self.column_mask = column_mask
        self.unaccounted = None
        self._data = []

        if self.group_column is None:
            this_group = GroupAgreement(self.dataframe, None, self.column_mask)
            self._data.append(this_group)
        else:
            grouped = self.dataframe.groupby(group_column)
            for key, group in grouped:
                this_group = GroupAgreement(group, key, self.column_mask)
                self._data.append(this_group)
            unaccounted_bool = self.dataframe[group_column].isnull()
            self.unaccounted = self.dataframe[unaccounted_bool]

    # pylint: disable=too-many-arguments
    @classmethod
    def from_file(cls, df_path: str, group_column: str = None,
                  column_names: List[str] = None, mask_first: str = None,
                  mask_last: str = None):
        """Create a DatasetAgreement object from file.

        This static method allows to initialize a DatasetAgreement
        object with more flexibility than the __init__ by accepting a
        path to the dataset and additional parameters to get the column
        masking correct.

        The resulting mask from inputs `column_mask`, `mask_first`, and
        `mask_last` is the set of columns that follow all conditions.

        Args:
            df_path: Path to the dataset. Currently only .csv and
                .xls(x) files are supported
            group_column: The column label for the column that defines
                which rows are in which groups. Default of None means
                the entire dataset is from the same group.
            column_names: A list of column labels for which columns to
                keep and do analysis on. Default of None means to use
                all columns.
            mask_first: The first possible column label to keep in the
                mask. This does not have to be in the column_mask.
                Default of None means start with the first column.
            mask_last: The last possible column label to keep in the
                mask. This does not have to be in the column_mask.
                Default of None means use through the last column.

        Returns:
            A properly initialized DatasetAgreement class.
        """
        if df_path.endswith('.csv'):
            dataframe = pd.read_csv(df_path)
        elif df_path.endswith(('.xls', '.xlsx')):
            dataframe = pd.read_excel(df_path)
        else:
            msg = (f'Unable to create dataset from "{df_path}". Known '
                   f'extensions are .csv, .xls, and .xlsx')
            raise TypeError(msg)
        mask = create_mask(dataframe, column_names, mask_first, mask_last)
        return cls(dataframe, group_column, mask)

    # pylint: disable=too-many-arguments
    @classmethod
    def from_file_and_odk(cls, df_path: str, odk_path: str,
                          group_column: str = None, mask_first: str = None,
                          mask_last: str = None, odk_sep: str = ':'):
        """Create a DatasetAgreement object for ODK data.

        This static method allows to initialize a DatasetAgreement
        object by using information from an ODK file to produce a
        column mask.

        The resulting mask from inputs `column_mask`, `mask_first`, and
        `mask_last` is the set of columns that follow all conditions.

        Args:
            df_path: Path to the dataset. Currently only .csv and
                .xls(x) files are supported
            odk_path: The path to the XlsForm associated with csv_path
            group_column: The column label for the column that defines
                which rows are in which groups. Default of None means
                the entire dataset is from the same group.
            mask_first: The first possible column label to keep in the
                mask. This does not have to be in the column_mask.
                Default of None means start with the first column.
            mask_last: The last possible column label to keep in the
                mask. This does not have to be in the column_mask.
                Default of None means use through the last column.
            odk_sep: The group prefix separator. ODK CSV files use
                either '-' or ':', depending on if ODK Briefcase or ODK
                Aggregate, respectively, creates the file.

        Returns:
            A properly initialized DatasetAgreement class.
        """
        if df_path.endswith('.csv'):
            dataframe = pd.read_csv(df_path)
        elif df_path.endswith(('.xls', '.xlsx')):
            dataframe = pd.read_excel(df_path)
        else:
            msg = (f'Unable to create dataset from "{df_path}". Known '
                   f'extensions are .csv, .xls, and .xlsx')
            raise TypeError(msg)
        type_name_labels = odk_response_rows(odk_path, odk_sep)
        names = [item.name for item in type_name_labels]
        column_mask = create_mask(dataframe, names, mask_first, mask_last)
        return cls(dataframe, group_column, column_mask)

    def group(self, key=None):
        """Return a stored dataset by group id.

        The group id is a unique value from the group_column as
        determined by Pandas when the source file is read into memory.

        If there is no group_column specified in __init__, then there
        is only one GroupAgreement object, and key should be None.

        Args:
             key: The unique group id for the group. Default is None
                for returning the first GroupAgreement.

        Returns:
            The GroupAgreement object associated with the key.
        """
        if key is None:
            return self[0]
        try:
            found = next((data for data in self if data.group_id == key))
            return found
        except StopIteration:
            raise KeyError(key)

    @property
    def group_ids(self) -> list:
        """Return the group IDs as a list."""
        return [group.group_id for group in self]

    def print_summary(self):
        """Print a summary of results."""
        for group_agreement in self:
            group_agreement.print_summary()

    def __getitem__(self, item: int) -> GroupAgreement:
        """Return group by index."""
        return self._data[item]

    def __iter__(self) -> Iterable[GroupAgreement]:
        """Get an iterator over the groups."""
        return iter(self._data)

    def __len__(self):
        """Get the number of groups."""
        return len(self._data)

    def __repr__(self):
        """Get a representation of this object."""
        return f'<DatasetAgreement, group count: {len(self)}>'


SKIPPED_ODK_TYPES = (
    'type',
    'calculate',
    'note',
    'start',
    'end',
    'deviceid',
    'simserial',
    'phonenumber',
    'hidden',
    '',
)


SKIPPED_ODK_TYPES_START = (
    'hidden ',
    'begin ',
    'end ',
)


def is_skipped_odk_type(odk_type: str) -> bool:
    """Check ODK question type if it is to be skipped.

    Certain ODK question types are not useful in comparing answers
    within a group. Therefore they are skipped. Examples are

    * note
    * calculate
    * hidden

    Some do not have values. Others do. None of these are used for
    comparison.

    This method uses module level SKIPPED_ODK_TYPES and
    SKIPPED_ODK_TYPES_START to determine what to skip.

    Args:
        odk_type: The "type" passed from a row in an ODK file.

    Returns:
        True if this type is to be skipped. For example, True is
        returned for the "note" type. False if otherwise.
    """
    skipped_type = any(i == odk_type for i in SKIPPED_ODK_TYPES)
    skipped_type_start = any(odk_type.startswith(i) for i in
                             SKIPPED_ODK_TYPES_START)
    return skipped_type or skipped_type_start


TypeNameLabel = namedtuple('TypeNameLabel', ['type', 'name', 'label'])


def odk_type_name_label(odk_path: str) -> List[TypeNameLabel]:
    """Return list of types, names, and labels in an XlsForm.

    Args:
        odk_path: The path to the XlsForm

    Returns:
        A list of tuples, one tuple per row, of the values for
        type, name, label.
    """
    book = xlrd.open_workbook(odk_path)
    survey = book.sheet_by_name('survey')
    first_row = survey.row_values(0)
    type_col_id = first_row.index('type')
    type_col = survey.col_values(type_col_id)
    name_col_id = first_row.index('name')
    name_col = survey.col_values(name_col_id)
    # This takes the first label column. Later, we could be take input to
    # choose a given translation or specific label or label::<language> column
    label_col_id = next(i for i, item in enumerate(first_row) if
                        item.startswith('label'))
    label_col = survey.col_values(label_col_id)
    zipped = zip(type_col, name_col, label_col)
    type_name_labels = [TypeNameLabel(*args) for args in zipped]
    return type_name_labels


def odk_response_rows(odk_path: str, odk_sep: str = ':') \
        -> List[TypeNameLabel]:
    """Return list of filtered types, names, and labels in an XlsForm.

    The routine filters the columns according to the skipped ODK types
    defined in this module.

    It also creates the full column name as would be found in a dataset
    with groups and repeats as prefixes.

    Args:
        odk_path: The path to the XlsForm
        odk_sep: The group prefix separator. ODK CSV files use
            either '-' or ':', depending on if ODK Briefcase or ODK
            Aggregate, respectively, creates the file.

    Returns:
        A list of tuples, one tuple per row, of the values for type,
        fully-qualified name, and label.
    """
    iterator = odk_type_name_label(odk_path)
    parent_segments = []
    filtered = []
    for item in iterator:
        if item.type in ('begin group', 'begin repeat'):
            parent_segments.append(item.name)
        elif item.type in ('end group', 'end repeat'):
            parent_segments.pop()
        elif not is_skipped_odk_type(item.type):
            all_segments = parent_segments + [item.name]
            new_name = odk_sep.join(all_segments)
            this_record = TypeNameLabel(item.type, new_name, item.label)
            filtered.append(this_record)
    return filtered


def create_mask(dataframe: pd.DataFrame, column_names: List[str] = None,
                mask_first: str = None, mask_last: str = None) -> List[str]:
    """Create a column mask, clipping with first and last columns.

    Args:
        dataframe: A dataframe for which to make a mask
        column_names: A list of possible column names to use. If None,
            then all column names are used.
        mask_first: The first possible column label to keep in the
            mask. This does not have to be in the column_names. Default
            of None means start with the first column.
        mask_last: The last possible column label to keep in the mask.
            This does not have to be in the column_names. Default of
            None means use through the last column.

    Returns:
        A list of strings of the column labels in the dataset. These
        strings are in the column mask and between mask_first and
        mask_last.
    """
    if mask_first is not None and mask_first not in dataframe:
        raise KeyError(mask_first)
    if mask_last is not None and mask_last not in dataframe:
        raise KeyError(mask_last)
    can_collect = False
    if mask_first is None:
        can_collect = True
    lookup = list(dataframe) if column_names is None else set(column_names)
    refined_mask = []
    for column in dataframe:
        if column == mask_first:
            can_collect = True
        if can_collect and column in lookup:
            refined_mask.append(column)
        if column == mask_last:
            can_collect = False
    return refined_mask
