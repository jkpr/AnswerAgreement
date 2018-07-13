"""Command-line interface for Answer Agreement Analysis."""
import argparse

from .aa import DatasetAgreement


def cli():
    """Run a CLI for this module."""
    prog_desc = 'Run an Answer Agreement Analysis on the command line.'
    parser = argparse.ArgumentParser(description=prog_desc)
    parser.add_argument('datafile', help='A file with the data for analysis')
    parser.add_argument('-x', '--xlsform', help=(
        'The XlsForm used to create this dataset. This is optional. Not all '
        'datasets come from ODK. If supplied, then the XlsForm information is '
        'used to remove points of comparison, such as "calculate" types.'
    ))
    parser.add_argument('-g', '--group_column', help=(
        'The column used to identify groups in the dataset. If not supplied, '
        'then the entire dataset is treated as from one group.'
    ))
    parser.add_argument('-f', '--first', help=(
        'The first column to start analyzing. If not supplied, then the first '
        'column of the dataset is used.'
    ))
    parser.add_argument('-l', '--last', help=(
        'The last column to analyze. If not supplied, then the last column of '
        'the dataset is used.'
    ))
    parser.add_argument('-s', '--separator', action='store_true', help=(
        'If option is supplied (with no argument!), then the separator is '
        'switched to the hyphen "-". By default, the colon ":" is used. This '
        'is only used if an ODK file is passed in.'
    ))
    args = parser.parse_args()
    if args.xlsform:
        sep = '-' if args.separator else ':'
        agree = DatasetAgreement.from_file_and_odk(args.datafile, args.xlsform,
                                                   args.group_column,
                                                   args.first, args.last, sep)
    else:
        agree = DatasetAgreement.from_file(args.datafile, args.group_column,
                                           mask_first=args.first,
                                           mask_last=args.last)
    agree.print_summary()
