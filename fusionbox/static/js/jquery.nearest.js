jQuery.fn.nearest = function(find_child, closest_parent)
{
  if ( typeof closest_parent == 'undefined' )
  {
    if ( $(document).find(find_child).length === 0 )
      return $([]);

    var current = $(this);
    var child = null;
    while ( current.length !== 0 )
    {
      child = current.find(find_child);
      if ( child.length )
      {
        return child;
      }

      if ( current.parent() == current )  break;
      current = current.parent();
    }

    //return an empty set:
    return $([]);
  }
  var closest = $(this).closest(closest_parent);
  if ( closest.filter(find_child).length )  return closest.filter(find_child);
  return closest.find(find_child);
};
