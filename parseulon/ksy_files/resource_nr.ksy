meta:
  id: sci0_nr
  bit-endian: le
  endian: le
seq:
  - id: resources
    type: resource_entry
    repeat: eos
types:
  resource_entry:
    seq:
      - id: number
        type: b11
      - id: type
        type: b5
        enum: resource_type
      - id: comp_size
        type: u2
      - id: decomp_size
        type: u2
      - id: comp_method
        type: u2
        enum: compression_methods
      - id: contents
        size: comp_size - 4
        type:
          switch-on: type
          cases:
            'resource_type::text': res_text
            _: res_unk
  res_unk:
    seq:
      - id: value
        size-eos: true
  res_text:
    seq:
      - id: value
        type: str
        size-eos: true
        encoding: ascii
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
  compression_methods:
    0: uncompressed
    1: lzw
    2: huffman
