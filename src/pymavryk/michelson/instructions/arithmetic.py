from typing import Callable
from typing import List
from typing import Tuple
from typing import Type
from typing import Union
from typing import cast

from py_ecc import optimized_bls12_381 as bls12_381

from pymavryk.context.abstract import AbstractContext
from pymavryk.michelson.instructions.base import MichelsonInstruction
from pymavryk.michelson.instructions.base import dispatch_types
from pymavryk.michelson.instructions.base import format_stdout
from pymavryk.michelson.stack import MichelsonStack
from pymavryk.michelson.types import BLS12_381_FrType
from pymavryk.michelson.types import BLS12_381_G1Type
from pymavryk.michelson.types import BLS12_381_G2Type
from pymavryk.michelson.types import BytesType
from pymavryk.michelson.types import IntType
from pymavryk.michelson.types import MumavType
from pymavryk.michelson.types import NatType
from pymavryk.michelson.types import OptionType
from pymavryk.michelson.types import PairType
from pymavryk.michelson.types import TimestampType
from pymavryk.michelson.types.base import MichelsonType


class AbsInstruction(MichelsonInstruction, prim='ABS'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = cast(IntType, stack.pop1())
        a.assert_type_equal(IntType)
        res = NatType.from_value(abs(int(a)))
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a], [res]))  # type: ignore
        return cls(stack_items_added=1)


class AddInstruction(MichelsonInstruction, prim='ADD'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a, b = cast(
            Tuple[
                Union[IntType, NatType, MumavType, TimestampType, BLS12_381_G1Type, BLS12_381_G2Type, BLS12_381_FrType],
                ...,
            ],
            stack.pop2(),
        )
        (res_type,) = dispatch_types(
            type(a),
            type(b),
            mapping={
                (NatType, NatType): (NatType,),
                (NatType, IntType): (IntType,),
                (IntType, NatType): (IntType,),
                (IntType, IntType): (IntType,),
                (TimestampType, IntType): (TimestampType,),
                (IntType, TimestampType): (TimestampType,),
                (MumavType, MumavType): (MumavType,),
                (BLS12_381_FrType, BLS12_381_FrType): (BLS12_381_FrType,),
                (BLS12_381_G1Type, BLS12_381_G1Type): (BLS12_381_G1Type,),
                (BLS12_381_G2Type, BLS12_381_G2Type): (BLS12_381_G2Type,),
            },
        )
        res_type = cast(
            Union[
                Type[IntType],
                Type[NatType],
                Type[TimestampType],
                Type[MumavType],
                Type[BLS12_381_G1Type],
                Type[BLS12_381_G2Type],
                Type[BLS12_381_FrType],
            ],
            res_type,
        )
        if issubclass(res_type, IntType):
            res = res_type.from_value(int(a) + int(b))  # type: ignore
        else:
            res = res_type.from_point(bls12_381.add(a.to_point(), b.to_point()))  # type: ignore
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a, b], [res]))  # type: ignore
        return cls(stack_items_added=1)


class EdivInstruction(MichelsonInstruction, prim='EDIV'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a, b = cast(
            Tuple[Union[IntType, NatType, MumavType, TimestampType], Union[IntType, NatType, MumavType, TimestampType]],
            stack.pop2(),
        )
        q_type, r_type = dispatch_types(
            type(a),
            type(b),
            mapping={  # type: ignore
                (NatType, NatType): (NatType, NatType),
                (NatType, IntType): (IntType, NatType),
                (IntType, NatType): (IntType, NatType),
                (IntType, IntType): (IntType, NatType),
                (MumavType, NatType): (MumavType, MumavType),
                (MumavType, MumavType): (NatType, MumavType),
            },
        )  # type: Tuple[Union[Type[IntType], Type[NatType], Type[TimestampType], Type[MumavType]], Union[Type[IntType], Type[NatType], Type[TimestampType], Type[MumavType]]]
        if int(b) == 0:
            res = OptionType.none(PairType.create_type(args=[q_type, r_type]))
        else:
            q, r = divmod(int(a), int(b))
            if r < 0:
                r += abs(int(b))
                q += 1
            items: List[MichelsonType] = [q_type.from_value(q), r_type.from_value(r)]
            res = OptionType.from_some(PairType.from_comb(items))
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a, b], [res]))  # type: ignore
        return cls(stack_items_added=1)


def execute_shift(prim: str, stack: MichelsonStack, stdout: List[str], shift: Callable[[Tuple[int, int]], int]):
    a, b = cast(Tuple[NatType, NatType], stack.pop2())
    a.assert_type_equal(NatType)
    b.assert_type_equal(NatType)
    assert int(b) < 257, f'shift overflow {int(b)}, should not exceed 256'
    c = shift((int(a), int(b)))
    res = NatType.from_value(c)
    stack.push(res)
    stdout.append(format_stdout(prim, [a, b], [res]))


class LslInstruction(MichelsonInstruction, prim='LSL'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        execute_shift(cls.prim, stack, stdout, lambda x: x[0] << x[1])  # type: ignore
        return cls(stack_items_added=1)


class LsrInstruction(MichelsonInstruction, prim='LSR'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        execute_shift(cls.prim, stack, stdout, lambda x: x[0] >> x[1])  # type: ignore
        return cls(stack_items_added=1)


class MulInstruction(MichelsonInstruction, prim='MUL'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a, b = cast(
            Tuple[Union[IntType, NatType, MumavType, BLS12_381_FrType, BLS12_381_G1Type, BLS12_381_G2Type], ...],
            stack.pop2(),
        )
        (res_type,) = dispatch_types(
            type(a),
            type(b),
            mapping={
                (NatType, NatType): (NatType,),
                (NatType, IntType): (IntType,),
                (IntType, NatType): (IntType,),
                (IntType, IntType): (IntType,),
                (MumavType, NatType): (MumavType,),
                (NatType, MumavType): (MumavType,),
                (NatType, BLS12_381_FrType): (BLS12_381_FrType,),
                (IntType, BLS12_381_FrType): (BLS12_381_FrType,),
                (BLS12_381_FrType, NatType): (BLS12_381_FrType,),
                (BLS12_381_FrType, IntType): (BLS12_381_FrType,),
                (BLS12_381_FrType, BLS12_381_FrType): (BLS12_381_FrType,),
                (BLS12_381_G1Type, BLS12_381_FrType): (BLS12_381_G1Type,),
                (BLS12_381_G2Type, BLS12_381_FrType): (BLS12_381_G2Type,),
            },
        )
        res_type = cast(
            Union[
                Type[IntType],
                Type[NatType],
                Type[TimestampType],
                Type[MumavType],
                Type[BLS12_381_FrType],
                Type[BLS12_381_G1Type],
                Type[BLS12_381_G2Type],
            ],
            res_type,
        )
        if issubclass(res_type, IntType):
            res = res_type.from_value(int(a) * int(b))  # type: ignore
        else:
            res = res_type.from_point(bls12_381.multiply(a.to_point(), int(b)))  # type: ignore
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a, b], [res]))  # type: ignore
        return cls(stack_items_added=1)


class NegInstruction(MichelsonInstruction, prim='NEG'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = cast(Union[IntType, NatType, BLS12_381_FrType, BLS12_381_G1Type, BLS12_381_G2Type], stack.pop1())
        (res_type,) = dispatch_types(
            type(a),
            mapping={
                (IntType,): (IntType,),
                (NatType,): (IntType,),
                (BLS12_381_FrType,): (BLS12_381_FrType,),
                (BLS12_381_G1Type,): (BLS12_381_G1Type,),
                (BLS12_381_G2Type,): (BLS12_381_G2Type,),
            },
        )
        if issubclass(res_type, IntType):
            res = IntType.from_value(-int(a))  # type: ignore
        else:
            res = res_type.from_point(bls12_381.neg(a.to_point()))  # type: ignore
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a], [res]))  # type: ignore
        return cls(stack_items_added=1)


class SubInstruction(MichelsonInstruction, prim='SUB'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a, b = cast(Tuple[Union[IntType, NatType, MumavType, TimestampType], ...], stack.pop2())
        (res_type,) = dispatch_types(
            type(a),
            type(b),
            mapping={  # type: ignore
                (NatType, NatType): (IntType,),
                (NatType, IntType): (IntType,),
                (IntType, NatType): (IntType,),
                (IntType, IntType): (IntType,),
                (TimestampType, IntType): (TimestampType,),
                (TimestampType, TimestampType): (IntType,),
                (MumavType, MumavType): (MumavType,),
            },
        )  # type: Tuple[Union[Type[IntType], Type[NatType], Type[TimestampType], Type[MumavType]]]
        res = res_type.from_value(int(a) - int(b))
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a, b], [res]))  # type: ignore
        return cls(stack_items_added=1)


class SubMumavInstruction(MichelsonInstruction, prim='SUB_MUMAV'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a, b = cast(Tuple[MumavType, MumavType], stack.pop2())
        a.assert_type_equal(MumavType)
        b.assert_type_equal(MumavType)
        try:
            res = OptionType.from_some(MumavType.from_value(int(a) - int(b)))
        except OverflowError:
            res = OptionType.none(MumavType)
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a, b], [res]))  # type: ignore
        return cls(stack_items_added=1)


class IntInstruction(MichelsonInstruction, prim='INT'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = stack.pop1()
        if isinstance(a, BytesType):
            res = IntType.from_value(int.from_bytes(bytes(a), 'big', signed=True))
        else:
            a = cast(Union[NatType, BLS12_381_FrType], a)
            a.assert_type_in(NatType, BLS12_381_FrType)
            res = IntType.from_value(int(a))
        stack.push(res)
        stdout.append(f'{cls.prim} / {repr(a)} => {repr(res)}')
        return cls(stack_items_added=1)


class IsNatInstruction(MichelsonInstruction, prim='ISNAT'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = cast(IntType, stack.pop1())
        a.assert_type_equal(IntType)
        if int(a) >= 0:
            res = OptionType.from_some(NatType.from_value(int(a)))
        else:
            res = OptionType.none(NatType)
        stack.push(res)
        stdout.append(format_stdout(cls.prim, [a], [res]))  # type: ignore
        return cls(stack_items_added=1)


class NatInstruction(MichelsonInstruction, prim='NAT'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = cast(BytesType, stack.pop1())
        a.assert_type_in(BytesType)
        res = NatType.from_value(int.from_bytes(bytes(a), 'big'))
        stack.push(res)
        stdout.append(f'{cls.prim} / {repr(a)} => {repr(res)}')
        return cls(stack_items_added=1)


class BytesInstruction(MichelsonInstruction, prim='BYTES'):
    @classmethod
    def execute(cls, stack: MichelsonStack, stdout: List[str], context: AbstractContext):
        a = cast(Union[NatType, IntType], stack.pop1())
        a.assert_type_in(NatType, IntType)
        int_val = int(a)
        signed = isinstance(a, IntType)
        if signed:
            length = (8 + (int_val + (int_val < 0)).bit_length()) // 8
        else:
            length = (7 + int_val.bit_length()) // 8
        # NOTE: the shortest big-endian encoding of natural number or integer n
        byte_val = int_val.to_bytes(length, 'big', signed=signed).lstrip(b'\x00')
        res = BytesType.from_value(byte_val)
        stack.push(res)
        stdout.append(f'{cls.prim} / {repr(a)} => {repr(res)}')
        return cls(stack_items_added=1)
