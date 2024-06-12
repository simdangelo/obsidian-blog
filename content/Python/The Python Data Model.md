---
title: The Python Data Model
tags:
  - python
---
# What we'll see
* By implementing **Special Methods**, your objects can behave like the built-in types, enabling the expressive coding style the community considers Pythonic.

# Python Data Model
> [!summary] Data Model
> **Data Model**: description of Python as a framework. It formalizes the interfaces of the building blocks of the language itself, such as sequences, functions, iterators, classes, and so on.
Python Data Model allows to write `len(collection)` instead of `collection.len()`. This apparent oddity is the tip of the entire Python Data Model and it's the key to everything we call **Pythonic**.

To create new classes, we leverage the Python Data Model and the Python Interpreter invokes **Special Methods** to perform basic object operations, often triggered by special syntax. The special method names are always written with leading and trailing double underscores. For example, in order to evaluate `my_collection[key]`, the interpreter calls `my_collection.__getitem__(key)`. We implement special methods when we want out objects to support and interact with fundamental language constructs.
Special methods are also called **Magic Methods** or **Dunder Methods** ("dunder" is a shortcut for double underscore before and after).
## Example about what "Pythonic" means
Le't show the power of implementing `__getitem__` and `__len__` inside a class:
```python
import collections

Card = collections.namedtuple("Card", ["rank", "suit"])

class FrenchDeck:
	ranks = [str(n) for n in range(2, 11)] + list("JQKA")
	suits = "spades diamonds clubs hearts".split()

	def __init__(self):
		self._cards = [Card(rank, suit) for suit in self.suits for rank in self.ranks]

	def __len__(self):
		return len(self._cards)

	def __getitem__(self, position):
		return self._cards[position]
```
Note that the reason of using `collections.namedtuple` is to provide a nice a representation for the cards in the deck:
```python
beer_card = Card('7', 'diamonds')
beer_card
```
Output:
```
Card(rank='7', suit='diamonds')
```

Let's instantiate a deck and see how many items it contains:
```python
deck = FrenchDeck()
len(deck)
```
Output:
```
52
```
Let's read a specific card from the deck:
```python
print(deck[0])
print(deck[-1])
```
Output:
```
Card(rank='2', suit='spades')
Card(rank='A', suit='hearts')
```
Furthermore, since `__getitem__` delegates to the `[]` operator, the deck automatically supports slicing and it makes it **iterable**:
```python
print(deck[:3])

for card in deck:
	print(card)
```
Output:
```
[Card(rank='2', suit='spades'), Card(rank='3', suit='spades'), Card(rank='4', suit='spades')]

Card(rank='2', suit='spades')
Card(rank='3', suit='spades')
Card(rank='4', suit='spades')
Card(rank='5', suit='spades')
...
```
To pick a random card from the deck we can use the Python built-in function `random.choice` to get a random number from a sequence:
```python
from random import choice

choice(deck)
```
Output:
```
Card(rank='10', suit='clubs')
```
Since with `__getitem__` dunder method, our class became an iterable, we can also use in **operator**:
```python
print(Card('Q', 'hearts') in deck)
print(Card('7', 'beast') in deck)
```
Output:
```
True
False
```
> [!info]- When an object is considered Iterable
> https://docs.python.org/3/glossary.html#term-iterable>
 
You can also use the build-in `sorted()` function:
```python
suit_values = dict(spades=3, hearts=2, diamonds=1, clubs=0)

def spades_high(card):
	rank_value = FrenchDeck.ranks.index(card.rank)
	return rank_value * len(suit_values) + suit_values[card.suit]

for card in sorted(deck, key=spades_high):
print(card)
```
Output:
```
Card(rank='2', suit='clubs')
Card(rank='2', suit='diamonds')
Card(rank='2', suit='hearts')
Card(rank='2', suit='spades')
Card(rank='3', suit='clubs')
...
```
> [!summary] Recap
> Advantages of using Dunder Methods:
> * users of your classes **don't have to memorize arbitrary method names for standard operations** (`.size()` or `.lenght()` or what to get the number of items?)
> * it's easier to **benefit from the rich Python Standard Library** and avoid reinventing the wheel, like `random.choice`.
> * by implementing the special methods `__len__` and `__getitme__`, the `FrenchDeck` **behaves like a standard Python Sequence** with obvious advantages:
> 	* iteration, slicing from core language features
> 	* usage of `random.choice`, `reversed`, `sorted`
# How Special Methods are used
Dunder methods are meant to be called the the Python Interpreter, not by any users. You don't write `an_object.__len__`, but you write `len(an_object)` and, if the `__len__` method is implemented, Python calls this method under the hood.

Special method call could be implicit. For example the statement `for i in x:` causes the invocation of `iter(x)`, which in turn calls `x.__iter__()` if it's available, or `x.__getitem__()` as it did in our example.

The only special method that is frequently called by user code directly is `__init__`.

It's always better to call built-in functions (e.g. `len`, `iter`, `str`, etc) instead of their corresponding special methods because they often provide other services and are faster than those method calls.