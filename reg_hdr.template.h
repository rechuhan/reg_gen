{%- set prefix = "{http://www.accellera.org/XMLSchema/IPXACT/1685-2014}" -%}
{%- set memoryMaps = root.find(prefix+"memoryMaps") -%}
{%- if not memoryMaps -%}
    {%- set prefix =  "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}" -%}
    {%- set memoryMaps = root.find(prefix+"memoryMaps") -%}
{%- endif %}
    {%- for one_map in memoryMaps.findall(prefix+"memoryMap") %}
        {%- for one_blk in one_map.findall(prefix+"addressBlock") %}
            {%- set blk_name = one_blk.find(prefix+"name").text -%}
            {%- set blk_base_address = one_blk.find(prefix+"addressBlock").text -%}
            {%- set blk_range = one_blk.find(prefix+"range").text -%}
            {%- set blk_width = one_blk.find(prefix+"width").text -%}
            {%- for one_reg in one_blk.findall(prefix+"register") %}
                {%- set reg_name = one_reg.find(prefix+"name").text -%}
                {%- set reg_offset = one_reg.find(prefix+"addressOffset").text -%}
                {%- set reg_access = one_reg.find(prefix+"access").text -%}
                {%- for one_field in one_reg.findall(prefix+"field") %}
                {%- endfor %}
            {%- endfor %}
const int {{blk_name}}_length = {{len(all_reset)}};
int {{blk_name}}_address[] = {
    0x{{"%x"%all_address[0]}}
        {%- for one_value in all_address[1:] %},
    0x{{"%x"%one_value}}
        {%- endfor %}
};
int {{blk_name}}_reset_value[] = {
    0x{{"%x"%all_reset[0]}}
        {%- for one_value in all_reset[1:] %},
    0x{{"%x"%one_value}}
        {%- endfor %}
};
int {{blk_name}}_w0_mask[] = {
    0x{{"%x"%all_w0_mask[0]}}
        {%- for one_value in all_w0_mask[1:] %},
    0x{{"%x"%one_value}}
        {%- endfor %}
};
int {{blk_name}}_w1_mask[] = {
    0x{{"%x"%all_w1_mask[0]}}
        {%- for one_value in all_w1_mask[1:] %},
    0x{{"%x"%one_value}}
        {%- endfor %}
};
    {%- endfor %}
{%- endfor %}

