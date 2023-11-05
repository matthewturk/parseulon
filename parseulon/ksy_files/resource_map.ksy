meta:
  id: sci0_map
  file-extension: "map"
  bit-endian: le
  endian: le
seq:
  - id: resources
    type: resource_record
    size: 6
    repeat: until
    repeat-until: _.fullvalue == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
types:
  resource_record:
    seq:
      - id: number
        type: b11
      - id: type
        type: b5
        enum: resource_type
      - id: offset
        type: b26
      - id: fileno
        type: b6
    instances:
      fullvalue:
        pos: 0
        size: 6
enums:
  resource_type:
    0: view
    1: picture
    2: script
    3: text
    4: sound
    5: unused
    6: vocab
    7: font
    8: cursor
    9: patch
