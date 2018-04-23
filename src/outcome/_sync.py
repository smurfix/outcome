# coding: utf-8
from __future__ import absolute_import, division, print_function

import abc
import attr
import inspect

from ._util import ABC, AlreadyUsedError

__all__ = ['Error', 'Outcome', 'Value', 'capture']


def capture(sync_fn, *args, **kwargs):
    """Run ``sync_fn(*args, **kwargs)`` and capture the result.

    Returns:
      Either a :class:`Value` or :class:`Error` as appropriate.

    """
    try:
        return Value(sync_fn(*args, **kwargs))
    except BaseException as exc:
        return Error(exc)

@attr.s(repr=False, init=False, slots=True)
class Outcome(ABC):
    """An abstract class representing the result of a Python computation.

    This class has two concrete subclasses: :class:`Value` representing a
    value, and :class:`Error` representing an exception.

    In addition to the methods described below, comparison operators on
    :class:`Value` and :class:`Error` objects (``==``, ``<``, etc.) check that
    the other object is also a :class:`Value` or :class:`Error` object
    respectively, and then compare the contained objects.

    :class:`Outcome` objects are hashable if the contained objects are
    hashable.

    """
    _unwrapped = attr.ib(default=False, cmp=False, init=False)
    _stack = attr.ib(default=[], cmp=False, init=False)

    def _set_unwrapped(self):
        if self._unwrapped:
            import pdb;pdb.set_trace()
            raise AlreadyUsedError
        self._stack.append(inspect.stack())
        object.__setattr__(self, '_unwrapped', True)


    @abc.abstractmethod
    def unwrap(self):
        """Return or raise the contained value or exception.

        These two lines of code are equivalent::

           x = fn(*args)
           x = Result.capture(fn, *args).unwrap()

        """

    @abc.abstractmethod
    def send(self, gen):
        """Send or throw the contained value or exception into the given
        generator object.

        Args:
          gen: A generator object supporting ``.send()`` and ``.throw()``
              methods.

        """


@attr.s(frozen=True, repr=False, slots=True)
class Value(Outcome):
    """Concrete :class:`Outcome` subclass representing a regular value.

    """

    value = attr.ib()
    """The contained value."""

    def __repr__(self):
        return 'Value({!r})'.format(self.value)

    def unwrap(self):
        self._set_unwrapped()
        return self.value

    def send(self, gen):
        self._set_unwrapped()
        return gen.send(self.value)


@attr.s(frozen=True, repr=False, slots=True)
class Error(Outcome):
    """Concrete :class:`Outcome` subclass representing a raised exception.

    """

    error = attr.ib(validator=attr.validators.instance_of(BaseException))
    """The contained exception object."""

    def __repr__(self):
        return 'Error({!r})'.format(self.error)

    def unwrap(self):
        self._set_unwrapped()
        raise self.error

    def send(self, it):
        self._set_unwrapped()
        return it.throw(self.error)

