from typing import Optional, Union, cast


# TODO: Remove after DataTypes and ValidatorsAttr is removed
def cast_xml_to_string(xml_value: Union[memoryview, bytes, bytearray, str]) -> str:
    """Cast XML value to a string.

    Args:
        xml_value (Union[memoryview, bytes, bytearray, str]): The XML value to cast.

    Returns:
        str: The XML value as a string.
    """
    if isinstance(xml_value, str):
        return xml_value
    if isinstance(xml_value, memoryview):
        return xml_value.tobytes().decode()
    if isinstance(xml_value, (bytes, bytearray)):
        return xml_value.decode()
    return cast(str, xml_value)


def xml_to_string(
    xml: Optional[Union[memoryview, bytes, bytearray, str]],
) -> Optional[str]:
    """Convert XML value to a string.

    Args:
        xml_value (Union[memoryview, bytes, bytearray, str]): The XML value to cast.

    Returns:
        str: The XML value as a string.
    """
    if xml is None:
        return None

    string = xml
    if isinstance(xml, memoryview):
        string = xml.tobytes().decode()
    elif isinstance(xml, (bytes, bytearray)):
        string = xml.decode()

    return cast(str, string)
