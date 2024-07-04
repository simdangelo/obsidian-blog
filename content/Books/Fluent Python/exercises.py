from dataclasses import dataclass, field

class ClubMember:
    name: str
    guests: list = field(default_factory=list)

@dataclass
class HackerClubMember(ClubMember):
    all_handles = set()
    handle: str = ''

    def __post__init__(self):
        cls = self.__class__
        if self.handle == '':
            self.handle = self.name.split()[0]
        if self.handle in cls.all_handles:
            msg = f"handle {self.handle!r} alreadt exists."
            raise ValueError(msg)
        cls.all_handles.add(self.handle)
