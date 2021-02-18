import time
import copy
from lxml import etree
import argparse
import os

argparser = argparse.ArgumentParser('Write ELG metadata and configuration information to local directory')
argparser.add_argument('--source-lang', action="store", required=True)
argparser.add_argument('--target-lang', action="store", required=True)
argparser.add_argument('--source-region', action="store")
argparser.add_argument('--target-region', action="store")
argparser.add_argument('--version', action="store", default="1.0")
args = argparser.parse_args()
langpair = tuple(sorted((args.source_lang, args.target_lang)))
    
responsible_person_surname = "Hardwick"
responsible_person_given_name = "Sam"
responsible_person_email = "sam.hardwick@iki.fi"
model_location = 'https://object.pouta.csc.fi/OPUS-MT-models/{}-{}/opus-2019-12-04.zip'
version = args.version
imagename = f"opus-mt-elg-{langpair[0]}-{langpair[1]}"
docker_location = f"https://hub.docker.com/repository/docker/helsinkinlp/{imagename}:{version}"
source_langcode = args.source_lang
source_region = args.source_region
target_langcode = args.target_lang
target_region = args.target_region

def append_elements(root, elements):
    for e in elements:
        root.append(copy.deepcopy(e))

write_metadata_record_identifier = False

ms_namespace_uri = "http://w3id.org/meta-share/meta-share/"
xsi_namespace_uri = "http://www.w3.org/2001/XMLSchema-instance"
xml_namespace_uri = "http://www.w3.org/XML/1998/namespace"
ms_prefix = "{%s}" % ms_namespace_uri
xsi_prefix = "{%s}" % xsi_namespace_uri
xsi_schemaLocation_qualified_name = etree.QName(xsi_namespace_uri, "schemaLocation")
xsi_schemaLocation = "http://w3id.org/meta-share/meta-share/ ../../../Schema/ELG-SHARE.xsd"

lang_en = {etree.QName(xml_namespace_uri, 'lang'): 'en'}

namespace_map = {'ms': ms_namespace_uri,
                 'xsi' : xsi_namespace_uri,
                 'xml': xml_namespace_uri}

def ms(tag): return ms_prefix + tag

def Element(name, text = None, **kwargs):
    if 'attribs' in kwargs:
        retval = etree.Element(name, kwargs['attribs'], nsmap = namespace_map)
    else:
        retval = etree.Element(name, nsmap = namespace_map)
    if text != None:
        retval.text = text
    return retval

def make_language(_id, **kwargs):
    language = Element("language")
    subtags = []
    if 'script' in kwargs:
        subtags.append(kwargs['script'])
        language.append(Element("scriptId", kwargs['script']))
    if 'region' in kwargs and kwargs['region']:
        subtags.append(kwargs['region'])
        language.append(Element("regionId", kwargs['region']))
    if 'variant' in kwargs:
        subtags.append(kwargs['variant'])
        language.append(Element("variantId", kwargs['variant']))
    tag = '-'.join([_id] + subtags)
    language.append(Element("languageId", _id))
    language.append(Element("languageTag", tag))
    return language

metadata = etree.Element(ms("MetadataRecord"),
                         { xsi_schemaLocation_qualified_name: xsi_schemaLocation },
                         nsmap=namespace_map)

if write_metadata_record_identifier:
    metadata.append(etree.Element(ms("MetadataRecordIdentifier"),
                                  { etree.QName(ms_namespace_uri, "MetadataRecordIdentifierScheme"): "http://w3id.org/meta-share/meta-share/elg" },
                                  nsmap = namespace_map))

creation_date = etree.SubElement(metadata, ms("metadataCreationDate"))
creation_date.text = time.strftime("%Y-%m-%d")

responsible_person = [
    Element(ms("actorType"), "Person"),
    Element(ms("surname"), responsible_person_surname, attribs = lang_en),
    Element(ms("givenName"), responsible_person_given_name, attribs = lang_en),
    Element(ms("email"), responsible_person_email)
    ]

creator = etree.SubElement(metadata, ms("metadataCreator"))
append_elements(creator, responsible_person)
curator = etree.SubElement(metadata, ms("metadataCurator"))
append_elements(curator, responsible_person)

metadata.append(Element(ms("compliesWith"), "http://w3id.org/meta-share/meta-share/ELG-SHARE"))

described_entity = etree.SubElement(metadata, ms("DescribedEntity"), nsmap = namespace_map)
language_resource = etree.SubElement(described_entity, ms("LanguageResource"), nsmap = namespace_map)
language_resource.append(Element(ms("resourceName"), "OPUS-MT: Open neural machine translation", attribs = lang_en, nsmap=namespace_map))
language_resource.append(Element(ms("resourceShortName"), "OPUS-MT", attribs = lang_en))
language_resource.append(Element(ms("description"), "Multilingual machine translation using neural networks.", attribs = lang_en))
language_resource.append(Element(ms("version"), version))
additional_info = etree.SubElement(language_resource, ms("additionalInfo"), nsmap = namespace_map)
additional_info.append(Element(ms("landingPage"), "https://github.com/Helsinki-NLP/Opus-MT"))
language_resource.append(Element(ms("keyword"), "machine translation", attribs = lang_en))
language_resource.append(Element(ms("keyword"), "translation", attribs = lang_en))
language_resource.append(Element(ms("keyword"), "multilingual", attribs = lang_en))

lr_subclass = etree.SubElement(language_resource, ms("LRSubclass"), nsmap = namespace_map)
tool_service = etree.SubElement(lr_subclass, ms("ToolService"), nsmap = namespace_map)
function = etree.SubElement(tool_service, ms("function"), nsmap = namespace_map)
function.append(Element(ms("LTClassRecommended"), "http://w3id.org/meta-share/omtd-share/MachineTranslation"))
software_distribution = etree.SubElement(tool_service, ms("SoftwareDistribution"), nsmap = namespace_map)
software_distribution.append(Element(ms("SoftwareDistributionForm"), "http://w3id.org/meta-share/meta-share/dockerImage"))
software_distribution.append(Element(ms("dockerDownloadLocation"), docker_location))
software_distribution.append(Element(ms("executionLocation"), f"http://localhost:8888/elg/translate/{source_langcode}/{target_langcode}"))

licence_terms = etree.SubElement(software_distribution, ms("licenceTerms"), nsmap = namespace_map)
licence_terms.append(Element(ms("licenceTermsName"), "MIT License", attribs = lang_en))
licence_terms.append(Element(ms("licenceTermsURL"), "https://spdx.org/licenses/MIT.html"))
licence_identifier = etree.Element(ms("LicenceIdentifier"),
                                   { etree.QName(ms_namespace_uri, "LicenceIdentifierScheme"): "http://w3id.org/meta-share/meta-share/SPDX" },
                                   nsmap = {'ms': ms_namespace_uri})
licence_identifier.text = "MIT"
licence_terms.append(licence_identifier)

tool_service.append(Element(ms("languageDependent"), "true"))

input_content_resource = etree.SubElement(tool_service, ms("inputContentResource"))
input_content_resource.append(Element(ms("processingResourceType"), "http://w3id.org/meta-share/meta-share/userInputText"))
input_content_resource.append(make_language(source_langcode, region = source_region))
input_content_resource.append(Element(ms("mediaType"), "http://w3id.org/meta-share/meta-share/text"))
input_content_resource.append(Element(ms("characterEncoding"), "http://w3id.org/meta-share/meta-share/UTF-8"))

output_content_resource = etree.SubElement(tool_service, ms("outputContentResource"))
output_content_resource.append(Element(ms("processingResourceType"), "http://w3id.org/meta-share/meta-share/userOutputText"))
output_content_resource.append(make_language(target_langcode, region = target_region))
output_content_resource.append(Element(ms("mediaType"), "http://w3id.org/meta-share/meta-share/text"))
output_content_resource.append(Element(ms("characterEncoding"), "http://w3id.org/meta-share/meta-share/UTF-8"))

tool_service.append(Element(ms("evaluated"), "false"))

with open(f"OPUS-MT-{source_langcode}-{target_langcode}.xml", "w") as xml_fobj:
    xml_fobj.write(str(etree.tostring(metadata, xml_declaration = True, encoding = 'utf-8', pretty_print = True), encoding = "utf-8"))

if not os.path.exists("models.txt"):
    with open("models.txt", "w") as models_fobj:
        models_fobj.write(model_location.format(source_langcode, target_langcode) + '\n')
        models_fobj.write(model_location.format(target_langcode, source_langcode) + '\n')

if not os.path.exists("image-name.txt"):
    with open("image-name.txt", "w") as imagename_fobj:
        imagename_fobj.write(f"{imagename}:{version}\n")
