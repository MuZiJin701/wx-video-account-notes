# ADR 0003: Default and self-deployed resolvers

Status: Accepted

The maintainer's resolver remains the default for every installation. Users may select their own server by configuring its endpoint and separate access key. A custom resolver failure does not silently fall back to the default, so the destination of a share link stays predictable. Both services only resolve links; media processing and note writing stay on the user's machine.
