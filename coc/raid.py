"""
MIT License

Copyright (c) 2019-2020 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import typing
from typing import List, TYPE_CHECKING

from . import BasePlayer
from .miscmodels import Badge, Timestamp, try_enum
from .utils import cached_property, correct_tag

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .war_members import ClanWarMember  # noqa


class RaidMember(BasePlayer):
    """Represents a Raid Member that the API returns.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    attack_count: :class:`int`
        The number of attacks from this player
    attack_limit: :class:`int`
        The limit of attacks from this player
    bonus_attack_limit: :class:`int`
        The limit of bonus attacks from this player
    capital_resources_looted:  :class:`int`
        The amount of resources looted by this player
    raid_log_entry: :class:`RaidLogEntry`
        The raid log entry this member is in
    """

    __slots__ = ("tag",
                 "name",
                 "attack_count",
                 "attack_limit",
                 "bonus_attack_limit",
                 "capital_resources_looted",
                 "raid_log_entry",
                 "_attacks",
                 "_client")

    def __init__(self, *, data, client, raid_log_entry):
        super().__init__(data=data, client=client)
        self._client = client
        self.raid_log_entry = raid_log_entry
        self._attacks = []
        self._from_data(data)

    def __repr__(self):
        attrs = [
            ("tag", self.tag),
            ("raid_log_entry", repr(self.raid_log_entry)),
            ("attack_count", self.attack_count)
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, RaidMember)
                and self.tag == other.tag
                and self.raid_log_entry == other.raid_log_entry
                and self.attacks == other.attacks)

    def _from_data(self, data):
        data_get = data.get

        self.name: str = data_get("name")
        self.tag: str = data_get("tag")
        self.attack_count: int = data_get("attacks")
        self.attack_limit: int = data_get("attackLimit")
        self.bonus_attack_limit: int = data_get("bonusAttackLimit")
        self.capital_resources_looted: int = data_get("capitalResourcesLooted")

    @property
    def attacks(self):
        """List[:class:`RaidAttack`]: The member's attacks in this raid log entry"""
        list_attacks = self._attacks  # type: List[RaidAttack]
        if list_attacks:
            return list_attacks

        list_attacks = list(attack for attack_raid in self.raid_log_entry.attack_log
                            for district in attack_raid.districts for attack in district.attacks
                            if attack and attack.attacker_tag == self.tag)
        self._attacks = list_attacks
        return list_attacks


class RaidAttack:
    """Represents a Raid attack

    Attributes
    ----------
    attacker_tag:
        :class:`str` - The attacker tag
    attacker_name:
        :class:`str` - The attacker name
    destruction:
        :class:`float`- The destruction achieved
    raid_log_entry:
        :class:`RaidLogEntry` - The raid log entry this attack belongs to
    raid_clan:
        :class:`RaidClan` - The raid clan this attack belongs to
    district:
        :class:`RaidDistrict` - The raid district this attack belongs to
    """

    __slots__ = ("raid_log_entry",
                 "raid_clan",
                 "district",
                 "raid_member",
                 "attacker_tag",
                 "attacker_name",
                 "destruction",
                 "_client")

    def __repr__(self):
        attrs = [
            ("raid_log_entry", repr(self.raid_log_entry)),
            ("raid_clan", repr(self.raid_clan)),
            ("district", repr(self.district)),
            ("attacker_tag", self.attacker_tag),
            ("destruction", self.destruction),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.raid_log_entry == other.raid_log_entry
                and self.raid_clan == other.raid_clan
                and self.district == other.district
                and self.attacker_tag == other.attacker_tag
                and self.destruction == other.destruction)

    def __init__(self, data, client, raid_log_entry, raid_clan, district):
        self.raid_log_entry = raid_log_entry
        self.raid_clan = raid_clan
        self.district = district
        self._client = client
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.attacker_tag = data["attacker"]["tag"]
        self.attacker_name = data["attacker"]["name"]
        self.destruction = data["destructionPercent"]

    @property
    def attacker(self) -> "RaidMember":
        """:class:`RaidMember`: Returns the attacking player."""
        return self.raid_log_entry.get_member(self.attacker_tag)


class RaidDistrict:
    """Represents a Raid Clan Capital District.

    Attributes
    -----------
    id:
        :class:`int`: The district's unique ID as given by the API.
    name:
        :class:`str`: The district's name.
    hall_level:
        :class:`str`: The district's hall level.
    destruction:
        :class:`float`: The districts destruction percentage
    attack_count:
        :class:`int`: The districts attack count
    looted:
        :class:`int`: The districts total looted
    attacks:
        List[:class:`RaidAttack`]: The attacks on this district. Can be empty due to missing parts in the api response
    raid_log_entry:
        :class:`RaidLogEntry` - The raid log entry this district belongs to
    raid_clan:
        :class:`RaidClan` - The raid clan this district belongs to
    """

    __slots__ = ("id",
                 "name",
                 "hall_level",
                 "destruction",
                 "attack_count",
                 "looted",
                 "attacks",
                 "raid_log_entry",
                 "raid_clan",
                 "_client")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id),
                 ("raid_log_entry", repr(self.raid_log_entry)),
                 ("raid_clan", repr(self.raid_clan)),
                 ("hall_level", self.hall_level),
                 ("destruction", self.destruction)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.id == other.id and \
               self.attack_count == other.attack_count and \
               self.destruction == other.destruction and \
               self.looted == other.looted and \
               self.hall_level == other.hall_level

    def __init__(self, *, data, client, raid_log_entry, raid_clan):
        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.hall_level: int = data.get("districtHallLevel")
        self.destruction: float = data.get("destructionPercent")
        self.attack_count: int = data.get("attackCount")
        self.looted: int = data.get("totalLooted")
        self.raid_log_entry = raid_log_entry  # type: RaidLogEntry
        self.raid_clan = raid_clan  # type: RaidClan
        self._client = client
        if data.get("attacks", None):
            self.attacks: List[RaidAttack] = [RaidAttack(data=adata, client=client,
                                                         raid_log_entry=self.raid_log_entry,
                                                         raid_clan=self.raid_clan, district=self)
                                              for adata in data.get("attacks")]
        else:
            self.attacks = []


class RaidClan:
    """Represents the clan object returned by clan raid seasons.

        Attributes
        ----------
        tag: :class:`str`
            The clan's tag
        name: :class:`str`
            The clan's name
        badge: :class:`Badge`
            The clan's badge
        level: :class:`int`
            The clan's level.
        attack_count: :class:`int`
            The number of attacks in the raid.
        district_count: :class:`int`
            The number of districts in the raid.
        destroyed_district_count: :class:`int`
            The number of destroyed districts in the raid.
        raid_log_entry:
            :class:`RaidLogEntry` - The raid log entry this attack belongs to
        """

    __slots__ = (
        "tag",
        "name",
        "badge",
        "level",
        "attack_count",
        "district_count",
        "destroyed_district_count",
        "raid_log_entry",
        "_districts",
        "_attacks",
        "_client",
        "_response_retry",
        "_cs_raid_districts",
        "_iter_raid_districts"
    )

    def __init__(self, *, data, client, raid_log_entry, **_):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("attacker", data.get("defender")).get("tag")
        self.name = data.get("attacker", data.get("defender")).get("name")
        self.badge = try_enum(Badge, data=data.get("attacker", data.get("defender")).get("badgeUrls"),
                              client=self._client)
        self.level = data.get("attacker", data.get("defender")).get("level")
        self.raid_log_entry = raid_log_entry
        self._attacks = []
        self._from_data(data)

    def __eq__(self, other):
        return (isinstance(other, RaidClan)
                and self.raid_log_entry == other.raid_log_entry
                and self.tag == other.tag
                and self.attack_count == other.attack_count
                and self.district_count == other.district_count
                and self.destroyed_district_count == other.destroyed_district_count
                and self.attacks == other.attacks)

    def __repr__(self):
        attrs = [
            ("tag", self.tag),
            ("name", self.name),
            ("raid_log_entry", repr(self.raid_log_entry))
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data):
        data_get = data.get

        self.attack_count: int = data_get("attackCount")
        self.district_count: int = data_get("districtCount")
        self.destroyed_district_count: int = data_get("districtsDestroyed")

        if data_get("districts"):
            self._iter_raid_districts = (RaidDistrict(data=data, client=self._client,
                                                      raid_log_entry=self.raid_log_entry, raid_clan=self) for
                                         data in data_get("districts"))
        else:
            self._iter_raid_districts = ()

    @cached_property("_cs_raid_districts")
    def districts(self) -> typing.List[RaidDistrict]:
        """List[:class:`RaidDistrict`]: A :class:`List` of :class:`RaidDistrict` that the clan
        attacked."""
        return list(self._iter_raid_districts)

    @property
    def attacks(self) -> typing.List[RaidAttack]:
        """List[:class:`RaidAttack`]: Returns all attacks in the raid against this clan."""
        list_attacks = self._attacks  # type: List[RaidAttack]
        if list_attacks:
            return list_attacks

        list_attacks = list(attack for district in self.districts for attack in district.attacks)
        self._attacks = list_attacks
        return list_attacks


class RaidLogEntry:
    """Represents a Clash of Clans Raid Log Entry

    Attributes
    ----------
    state:
        :class:`str`: The state of the raid log entry
    start_time:
        :class:`Timestamp`: The :class:`Timestamp` that the raid started at.
    end_time:
        :class:`Timestamp`: The :class:`Timestamp` that the raid ended at.
    total_loot:
        :class:`int`: The amount of total loot
    completed_raid_count:
        :class:`int`: The number of completed raids
    attack_count:
        :class:`int`: The total number of attacks
    destroyed_district_count:
        :class:`int`: The number of destroyed enemy districts
    offensive_reward:
        :class:`int`: The amount of offensive reward
    defensive_reward:
        :class:`int`: The amount of defensive reward
    """

    __slots__ = ("state",
                 "start_time",
                 "end_time",
                 "total_loot",
                 "completed_raid_count",
                 "attack_count",
                 "destroyed_district_count",
                 "offensive_reward",
                 "defensive_reward",

                 "_cs_attack_log",
                 "_cs_defense_log",
                 "_cs_members",
                 "_iter_members",
                 "_iter_attack_log",
                 "_iter_defense_log",
                 "_members",
                 "_attack_log",
                 "_defense_log",
                 "_client",
                 "_response_retry")

    def __init__(self, *, data, client, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._from_data(data)
        self._members = {}
        self._attack_log = []
        self._defense_log = []

    def __repr__(self):
        attrs = [
            ("state", self.state),
            ("start_time", self.start_time),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, RaidLogEntry)
                and self.start_time == other.start_time
                and self._attack_log == other.attack_log
                and self._defense_log == other.defense_log
                and self.members == other.members)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.state: str = data_get("state")
        self.start_time = try_enum(Timestamp, data=data_get("startTime"))
        self.end_time = try_enum(Timestamp, data=data_get("endTime"))
        self.total_loot: int = data_get("capitalTotalLoot")
        self.completed_raid_count: int = data_get("raidsCompleted")
        self.attack_count: int = data_get("totalAttacks")
        self.destroyed_district_count: int = data_get("enemyDistrictsDestroyed")
        self.offensive_reward: int = data_get("offensiveReward")
        self.defensive_reward: int = data_get("defensiveReward")

        self._iter_attack_log = (RaidClan(data=adata, raid_log_entry=self, client=self._client)
                                 for adata in data_get("attackLog", []))
        self._iter_defense_log = (RaidClan(data=adata, raid_log_entry=self, client=self._client)
                                  for adata in data_get("defenseLog", []))

        self._iter_members = (RaidMember(data=adata, raid_log_entry=self, client=self._client)
                              for adata in data_get("members", []))

    @cached_property("_cs_members")
    def members(self) -> typing.List[RaidMember]:
        """List[:class:`RaidMember`]: A list of members that are in the raid.
        """
        dict_members = self._members = {m.tag: m for m in self._iter_members}
        return list(dict_members.values())

    @cached_property("_cs_attack_log")
    def attack_log(self) -> typing.List[RaidClan]:
        """List[:class:`RaidClan`]: A list of raid clans that are attacked in the raid season.
        """
        dict_attack_log = self._attack_log = {m.tag: m for m in self._iter_attack_log}
        return list(dict_attack_log.values())

    @cached_property("_cs_defense_log")
    def defense_log(self) -> typing.List[RaidClan]:
        """List[:class:`RaidClan`]: A list of raid clans which represents all the defensive raids of a season.
        """
        dict_defense_log = self._defense_log = {m.tag: m for m in self._iter_defense_log}
        return list(dict_defense_log.values())

    def get_member(self, tag: str) -> typing.Optional[RaidMember]:
        """Get a member of the clan for the given tag, or ``None`` if not found.

        Returns
        --------
        The clan member who matches the tag.: Optional[:class:`RaidMember`]"""
        tag = correct_tag(tag)
        if not self._members:
            _ = self.members

        try:
            return self._members[tag]
        except KeyError:
            return None


class RaidLog:
    """Represents a Generator for a RaidLog"""

    def __init__(self, clan_tag, client, data, cls):
        self.clan_tag = clan_tag
        self.data = data.get("items", [])
        self.client = client
        self.cls = cls
        self.global_index = 0
        self.max_index = len(self.data)
        self.next_page = data.get("paging").get("cursors").get("after", "")

    def __getitem__(self, item: int):
        if self.global_index > item:
            data = self.client.loop.run_until_complete(self.client.http.get_clan_raidlog(self.clan_tag, limit=item+1))
            self.data = data.get("items", [])
            self.max_index = len(self.data)
            self.next_page = data.get("paging").get("cursors").get("after", "")
            self.global_index = 0
            return_value = self.cls(data=self.data[item], client=self.client)
        elif self.global_index + self.max_index <= item and not self.next_page:
            raise IndexError()
        elif self.next_page and self.global_index + self.max_index <= item:
            data = self.client.loop.run_until_complete(self.client.http.get_clan_raidlog(self.clan_tag,
                                                                                         after=self.next_page,
                                                                                         limit=item-self.global_index))
            self.data = data.get("items", [])
            self.global_index += self.max_index
            self.max_index = len(self.data)
            self.next_page = data.get("paging").get("cursors").get("after", "")
            return_value = self.cls(data=self.data[item-self.global_index], client=self.client)
        elif self.global_index < item:
            return_value = self.cls(data=self.data[item-self.global_index], client=self.client)
        else:
            return_value = self.cls(data=self.data[item], client=self.client)
        return return_value
