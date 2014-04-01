

def traverse_related_to_field(field_name, model):
    '''
    Given an orm relational representation 'relational_field__field_name' and the base model of
    the relation, return the actual terminal Field
    '''
    jumps = field_name.split("__")
    if len(jumps) is 1:
        return model._meta.get_field_by_name(field_name)[0]
    else:
        return traverse_related_to_field("__".join(jumps[1:]),
                                        model._meta.get_field_by_name(jumps[:1][0])[0].rel.to
        )
