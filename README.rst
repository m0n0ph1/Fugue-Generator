
Creates species counterpoint with genetic algorithms.
To install type::

    $ python setup.py install

Once installed try::

    $ foox --help

for more information, or, to evolve some counterpoint try::

    $ foox -s 1 -cf 5 7 6 5 8 7 9 8 7 6 5 -o first_species
    $ lilypond first_species.ly

This will produce two files: first_species.pdf (the musical score) and
first_species.midi (a midi file to listen to with you media player).
