# Record codecs

Read docs/INDEX.md and docs/SPEC.md. The 32 group modules each contain six independent format pairs. record_codecs/primitives.py and record_codecs/examples.py are complete. The package dispatch imports only the requested group, and no group imports another group. All runtime code uses Python's standard library. Public tests contain one literal example per format.
