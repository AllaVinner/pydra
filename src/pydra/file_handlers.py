""" 
file_handlers

Main usage is to use with a CLI, e.g. with click when a file
is either read or written from/to a file or stdin/out/err.


Examples:
    With Click::

        >>> import click
        >>> from pydra.file_handlers import open_or_stdin
        >>> click.option(
        ...     "--input-file",
        ...     type=click.Path(path_type=str),
        ...     ...
        ... )
        >>> def my_command(input_file, ...):
        ...     with open_or_std(input_file) as f:
        ...         ...

"""
import sys
from pathlib import Path
from typing import Optional, IO, Union, Iterator
from contextlib import contextmanager

########################################
# Private
########################################

def _open_or_default(
    file: Optional[Union[str, Path]], mode: str, default: IO
) -> Iterator[IO]:
    """Open a file by path with IO default. Yield open file as generator.

    This function is used to create file context managers that defaults to stdin, stdout, and stderr.

    Args:
        file (Optional[Union[str, Path]]): Path to file to open. If `None`, use `default` instead of open file.
        mode (str): Mode to open file in. E.g. `"r", "w", "a"`.
        default (IO): IO to use as default.

    Yields:
        IO: Open IO file to us in context manager.
    """
    if file is not None:
        # Convert to Path if it's a string
        if isinstance(file, str):
            file = Path(file)

        # Open the file and yield it
        f = open(file, mode)
        try:
            yield f
        finally:
            f.close()
    else:
        # Just yield stdin
        yield default

########################################
# Public
########################################

@contextmanager
def open_or_stdin(file: Optional[Union[str, Path]] = None) -> Iterator[IO]:
    """Context manager that opens a file if provided, otherwise uses sys.stdin.

    Args:
        file (Optional[Union[str, Path]], None): File to open.

    Yields:
        IO: Open IO file
    """
    return _open_or_default(file, "rt", sys.stdin)


@contextmanager
def open_or_stdout(file: Optional[Union[str, Path]] = None) -> Iterator[IO]:
    """Context manager that opens a file if provided, otherwise uses sys.stdout.

    Args:
        file (Optional[Union[str, Path]], None): File to open.

    Yields:
        IO: Open IO file
    """
    return _open_or_default(file, "wt", sys.stdout)


@contextmanager
def open_or_stderr(file: Optional[Union[str, Path]] = None) -> Iterator[IO]:
    """Context manager that opens a file if provided, otherwise uses sys.stderr.

    Args:
        file (Optional[Union[str, Path]], None): File to open.

    Yields:
        IO: Open IO file
    """
    return _open_or_default(file, "at", sys.stderr)
