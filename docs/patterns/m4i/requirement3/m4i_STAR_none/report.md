| Level | Rule Name | Subject | Property | Value |
| --- | --- | --- | --- | --- |
| ERROR | missing_label | BFO:0000050 | rdfs:label |  |
| ERROR | missing_label | BFO:0000051 | rdfs:label |  |
| ERROR | missing_label | RO:0000056 | rdfs:label |  |
| ERROR | missing_label | RO:0000057 | rdfs:label |  |
| ERROR | missing_label | http://w3id.org/nfdi4ing/metadata4ing#inProject | rdfs:label |  |
| ERROR | missing_label | http://w3id.org/nfdi4ing/metadata4ing#projectParticipant | rdfs:label |  |
| ERROR | missing_label | rdf:PlainLiteral | rdfs:label |  |
| ERROR | missing_label | xsd:string | rdfs:label |  |
| ERROR | missing_label | skos:definition | rdfs:label |  |
| ERROR | missing_label | skos:editorialNote | rdfs:label |  |
| ERROR | missing_label | skos:example | rdfs:label |  |
| ERROR | missing_label | skos:note | rdfs:label |  |
| ERROR | missing_label | skos:prefLabel | rdfs:label |  |
| ERROR | missing_label | prov:Association | rdfs:label |  |
| ERROR | missing_label | prov:Role | rdfs:label |  |
| ERROR | missing_label | prov:qualifiedAssociation | rdfs:label |  |
| ERROR | missing_label | foaf:Agent | rdfs:label |  |
| ERROR | missing_label | foaf:Organization | rdfs:label |  |
| ERROR | missing_label | foaf:Person | rdfs:label |  |
| ERROR | missing_ontology_description | http://w3id.org/nfdi4ing/metadata4ing# | dc:description |  |
| ERROR | missing_ontology_license | http://w3id.org/nfdi4ing/metadata4ing# | dc:license |  |
| ERROR | missing_ontology_title | http://w3id.org/nfdi4ing/metadata4ing# | dc:title |  |
| ERROR | multiple_labels | prov:hadRole | rdfs:label | had role@en |
| ERROR | multiple_labels | prov:hadRole | rdfs:label | hatte Rolle@de |
| ERROR | multiple_labels | prov:wasRoleIn | rdfs:label | war Rolle in@de |
| ERROR | multiple_labels | prov:wasRoleIn | rdfs:label | wasRoleIn@en |
| WARN | annotation_whitespace | prov:qualifiedAssociation | skos:example | "Example application in m4i: |
| :SomeProcess |  |  |  |  |
|     a m4i:ProcessingStep;  |  |  |  |  |
|     obo:RO_0000057 :SomePerson; |  |  |  |  |
|     prov:qualifiedAssociation [ |  |  |  |  |
|         a prov:Association; |  |  |  |  |
|         prov:agent   :SomePerson; |  |  |  |  |
|         prov:hadRole :SomeRole; |  |  |  |  |
|         rdfs:comment \"":SomePerson had the :SomeRole in this :SomeProcess\""@en |  |  |  |  |
|     ]. |  |  |  |  |
|  |  |  |  |  |
| The direct relation between an activity and an agent expressed with 'has participant' (http://purl.obolibrary.org/obo/RO_0000057) does not give details about the agent's role in that activity. Using the property prov:qualifiedAssociation one can point to a blank node (cf. https://en.wikipedia.org/w/index.php?title=Blank_node&oldid=1015446558) containing additional information about the participation relation. |  |  |  |  |
| @en" |  |  |  |  |
| WARN | missing_definition | BFO:0000050 | IAO:0000115 |  |
| WARN | missing_definition | BFO:0000051 | IAO:0000115 |  |
| WARN | missing_definition | RO:0000056 | IAO:0000115 |  |
| WARN | missing_definition | RO:0000057 | IAO:0000115 |  |
| WARN | missing_definition | http://w3id.org/nfdi4ing/metadata4ing#inProject | IAO:0000115 |  |
| WARN | missing_definition | http://w3id.org/nfdi4ing/metadata4ing#projectParticipant | IAO:0000115 |  |
| WARN | missing_definition | rdf:PlainLiteral | IAO:0000115 |  |
| WARN | missing_definition | xsd:string | IAO:0000115 |  |
| WARN | missing_definition | skos:definition | IAO:0000115 |  |
| WARN | missing_definition | skos:editorialNote | IAO:0000115 |  |
| WARN | missing_definition | skos:example | IAO:0000115 |  |
| WARN | missing_definition | skos:note | IAO:0000115 |  |
| WARN | missing_definition | skos:prefLabel | IAO:0000115 |  |
| WARN | missing_definition | prov:Association | IAO:0000115 |  |
| WARN | missing_definition | prov:Role | IAO:0000115 |  |
| WARN | missing_definition | prov:hadRole | IAO:0000115 |  |
| WARN | missing_definition | prov:qualifiedAssociation | IAO:0000115 |  |
| WARN | missing_definition | prov:wasRoleIn | IAO:0000115 |  |
| WARN | missing_definition | foaf:Agent | IAO:0000115 |  |
| WARN | missing_definition | foaf:Organization | IAO:0000115 |  |
| WARN | missing_definition | foaf:Person | IAO:0000115 |  |
| INFO | missing_superclass | prov:Association | rdfs:subClassOf |  |
| INFO | missing_superclass | prov:Role | rdfs:subClassOf |  |
| INFO | missing_superclass | foaf:Agent | rdfs:subClassOf |  |