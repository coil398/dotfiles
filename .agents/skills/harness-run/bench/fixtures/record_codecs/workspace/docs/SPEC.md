# Record format specification

## 1. API and scope

There are 192 graded formats r001–r192, six per group module. Each has encode_rNNN(record: dict) -> dict and decode_rNNN(payload: dict) -> dict. The package API is encode(format_id, record) and decode(format_id, payload). Unknown format IDs raise KeyError. No group is imported until requested. examples.py contains two additional, ungraded formats.

## 2. Field tables

Each row in the linked group tables defines one field, giving source key, wire key, conversion, missing policy and null policy. Encode reads source keys and writes wire keys; decode reverses those keys. Only the four specified output keys may appear; unknown input keys are ignored. Field order is table order. Inputs contain valid values for the declared conversions, apart from missing or None values described below; malformed non-null values are outside this task.

## 3. Conversions

text: preserve the string exactly, including empty and Unicode strings.
decimal: encode a signed integer as its canonical base-10 string (zero is "0", no plus sign or padding); decode the canonical string to an integer. Integers have arbitrary precision.
boolean: the table supplies [true_token, false_token]; encode True/False to those exact strings, decode them to bool.
enum: the table supplies a source-to-wire map; encode by that map, decode by its inverse.
scale: the table supplies a positive integer multiplier; encode by multiplication, decode by exact integer division. Wire inputs are divisible by the multiplier. No floating point is used.
strings: copy the list of strings, preserving empty strings, Unicode, duplicates and order; an empty list stays empty.

## 4. Missing and null

Apply policies independently in both directions before conversion. missing=omit means do not emit the field; missing=required raises KeyError with the missing input key as its only argument. missing=default(value) is specified in SOURCE representation: encode emits its converted wire value, decode emits the source default. Each list default is a fresh copy on each call. None is not missing. null=preserve emits None without conversion; null=omit emits no key; null=reject raises ValueError with that direction's input key as its only argument. Process fields in table order if several errors are possible.

## 5. Ownership and boundary values

Neither direction mutates its input dictionary or any list within it. Each call returns a fresh dictionary; every emitted string list (including defaults) is independent of the input and of other calls. Negative integers, zero, arbitrarily large integers, empty strings and lists, duplicate strings, False and every listed enum member are supported.
