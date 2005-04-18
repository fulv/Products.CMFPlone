#
# Plone CatalogTool
#

from Products.CMFCore.CatalogTool import CatalogTool as BaseTool
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFPlone import ToolNames
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import aq_inner
from Acquisition import aq_parent

from Products.CMFCore.CatalogTool import _mergedLocalRoles
from Products.CMFCore.interfaces.portal_catalog \
        import IndexableObjectWrapper as IIndexableObjectWrapper
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFPlone import base_hasattr
from OFS.IOrderSupport import IOrderedContainer
from ZODB.POSException import ConflictError

from Products.ZCatalog.ZCatalog import ZCatalog

from AccessControl.Permissions import manage_zcatalog_entries as ManageZCatalogEntries
from AccessControl.PermissionRole import rolesForPermissionOn

from Acquisition import aq_base


# Use TextIndexNG2 if installed
try: 
    import Products.TextIndexNG2
    txng_version = 2
except ImportError:
    txng_version = 0


class ExtensibleIndexableObjectRegistry(dict):
    """Registry for extensible object indexing
    """
    
    def register(self, name, callable):
        """Register a callable method for an attribute.
        
        The method will be called with the object as first argument and
        additional keyword arguments like portal and the workflow vars.
        """
        self[name] = callable
        
    def unregister(self, name):
        del self[name]

_eioRegistry = ExtensibleIndexableObjectRegistry()
registerIndexableAttribute = _eioRegistry.register


class ExtensibleIndexableObjectWrapper(object):
    """Extensible wrapper for object indexing
    
    vars - additional vars as a dict, used for workflow vars like review_state
    obj - the indexable object
    portal - the portal root object
    registry - a registry 
    **kwargs - additional keyword arguments
    """
    
    __implements__ = IIndexableObjectWrapper
    
    def __init__(self, vars, obj, portal, registry = _eioRegistry, **kwargs):
        self._vars = vars
        self._obj = obj
        self._portal = portal
        self._registry = registry
        self._kwargs = kwargs
        
    def beforeGetattrHook(self, vars, obj, kwargs):
        return vars, obj, kwargs
        
    def __getattr__(self, name):
        vars = self._vars
        obj = self._obj
        kwargs = self._kwargs
        registry = self._registry
        
        vars, obj, kwargs = self.beforeGetattrHook(vars, obj, kwargs)
        
        if registry.has_key(name):
            return registry[name](obj, portal=self._portal, vars=vars, **kwargs)
        if vars.has_key(name):
            return vars[name]
        return getattr(obj, name)


def allowedRolesAndUsers(obj, portal, **kwargs):
    """
    Return a list of roles and users with View permission.
    Used by PortalCatalog to filter out items you're not allowed to see.
    """
    allowed = {}
    for r in rolesForPermissionOn('View', obj):
        allowed[r] = 1
    try:
        localroles = portal.acl_users._getAllLocalRoles(obj)
    except AttributeError:
        localroles = _mergedLocalRoles(obj)
    for user, roles in localroles.items():
        for role in roles:
            if allowed.has_key(role):
                allowed['user:' + user] = 1
    if allowed.has_key('Owner'):
        del allowed['Owner']
    return list(allowed.keys())

registerIndexableAttribute('allowedRolesAndUsers', allowedRolesAndUsers)


def getObjPositionInParent(obj, **kwargs):
    """Helper method for catalog based folder contents
    """
    parent = aq_parent(aq_inner(obj))
    if IOrderedContainer.isImplementedBy(parent):
        try:
            return parent.getObjectPosition(obj.getId())
        except ConflictError:
            raise
        except:
            pass
            # XXX log
    return 0

registerIndexableAttribute('getObjPositionInParent', getObjPositionInParent)


SIZE_CONST = {'kB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
SIZE_ORDER = ('GB', 'MB', 'kB')

def getObjSize(obj, **kwargs):
    """Helper method for catalog based folder contents
    """
    smaller = SIZE_ORDER[-1]

    if base_hasattr(obj, 'get_size'):
        size=obj.get_size()
    else:
        size = 0
    
    # if the size is a float, then make it an int
    # happens for large files
    try:
        size = int(size)
    except (ValueError, TypeError):
        pass
    
    if not size:
        return '0 %s' % smaller
    
    if isinstance(size, (int, long)):
        if size < SIZE_CONST[smaller]:
            return '1 %s' % smaller
        for c in SIZE_ORDER:
            if size/SIZE_CONST[c] > 0:
                break
        return '%.1f %s' % (float(size/float(SIZE_CONST[c])), c)
    return size

registerIndexableAttribute('getObjSize', getObjSize)


class CatalogTool(PloneBaseTool, BaseTool):

    meta_type = ToolNames.CatalogTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/book_icon.gif'
    
    __implements__ = (PloneBaseTool.__implements__, BaseTool.__implements__)

    def __init__(self):
        ZCatalog.__init__(self, self.getId())
        self._initIndexes()
        
    security.declarePublic('enumerateIndexes') 
    def enumerateIndexes(self):

        return ( ('Subject', 'KeywordIndex')
               , ('Creator', 'FieldIndex')
               , ('Date', 'DateIndex')
               , ('Type', 'FieldIndex')
               , ('created', 'DateIndex')
               , ('effective', 'DateIndex')
               , ('expires', 'DateIndex')
               , ('modified', 'DateIndex')
               , ('allowedRolesAndUsers', 'KeywordIndex')
               , ('review_state', 'FieldIndex')
               , ('in_reply_to', 'FieldIndex')
               , ('meta_type', 'FieldIndex')
               , ('id', 'FieldIndex')
               , ('getId', 'FieldIndex')
               , ('path', 'ExtendedPathIndex')
               , ('portal_type', 'FieldIndex')
               , ('getObjPositionInParent', 'FieldIndex')
               )

    def _removeIndex(self, index):
        """ Safe removal of an index """
        try: self.manage_delIndex(index)
        except: pass

    def manage_afterAdd(self, item, container):
        self._createTextIndexes(item, container)
               
    def _createTextIndexes(self, item, container):
        """ In addition to the standard indexes we need to create 
            'SearchableText', 'Title' and 'Description' either as
            TextIndexNG2 or ZCTextIndex instance
        """

        class args:
            def __init__(self, **kw):
                self.__dict__.update(kw)
            def keys(self):
                return self.__dict__.keys()

        # We need to remove the indexes to keep the tests working...baaah
        for idx in ('SearchableText', 'Title', 'Description'):
            self._removeIndex(idx)

        if txng_version == 2:

            # Prefer TextIndexNG V2 if available instead of ZCTextIndex 

            extra = args(default_encoding='utf-8')
            self.manage_addIndex('SearchableText', 'TextIndexNG2', 
                                  extra=args(default_encoding='utf-8', 
                                             use_converters=1, autoexpand=1))
            self.manage_addIndex('Title', 'TextIndexNG2', extra=extra)
            self.manage_addIndex('Description', 'TextIndexNG2', extra=extra)

        else:

            # ZCTextIndex as fallback

            if item is self and not hasattr(aq_base(self), 'plone_lexicon'):

                self.manage_addProduct[ 'ZCTextIndex' ].manage_addLexicon(
                    'plone_lexicon',
                    elements=[
                    args(group= 'Case Normalizer' , name= 'Case Normalizer' ),
                    args(group= 'Stop Words' , name= " Don't remove stop words" ),
                    args(group= 'Word Splitter' , name= "Unicode Whitespace splitter" ),
                    ]
                    )

                extra = args( doc_attr = 'SearchableText',
                              lexicon_id = 'plone_lexicon',
                              index_type  = 'Okapi BM25 Rank' )
                self.manage_addIndex('SearchableText', 'ZCTextIndex', extra=extra)

                extra = args( doc_attr = 'Description',
                              lexicon_id = 'plone_lexicon',
                              index_type  = 'Okapi BM25 Rank' )
                self.manage_addIndex('Description', 'ZCTextIndex', extra=extra)

                extra = args( doc_attr = 'Title',
                              lexicon_id = 'plone_lexicon',
                              index_type  = 'Okapi BM25 Rank' )
                self.manage_addIndex('Title', 'ZCTextIndex', extra=extra)

    security.declareProtected(ManagePortal, 'migrateIndexes')
    def migrateIndexes(self):
        """ Recreate all indexes """
        self._initIndexes()
        self._createTextIndexes()

    def _listAllowedRolesAndUsers( self, user ):
        # Makes sure the list includes the user's groups
        result = list( user.getRoles() )
        if hasattr(aq_base(user), 'getGroups'):
            result = result + ['user:%s' % x for x in user.getGroups()]
        result.append( 'Anonymous' )
        result.append( 'user:%s' % user.getId() )
        return result

    security.declarePrivate('indexObject')
    def indexObject(self, object, idxs=[]):
        '''Add object to catalog.
        The optional idxs argument is a list of specific indexes
        to populate (all of them by default).
        '''
        self.reindexObject(object, idxs)

    security.declarePrivate('reindexObject')
    def reindexObject(self, object, idxs=[], update_metadata=1):
        '''Update catalog after object data has changed.
        The optional idxs argument is a list of specific indexes
        to update (all of them by default).
        The update_metadata flag controls whether the object's
        metadata record is updated as well.
        '''
        url = self.__url(object)
        if idxs != []:
            # Filter out invalid indexes.
            valid_indexes = self._catalog.indexes.keys()
            idxs = [i for i in idxs if i in valid_indexes]
        self.catalog_object(object, url, idxs, update_metadata)

    security.declareProtected(ManageZCatalogEntries, 'catalog_object')
    def catalog_object(self, object, uid, idxs=[], update_metadata=1):
        # Wraps the object with workflow and accessibility
        # information just before cataloging.
        wf = getattr(self, 'portal_workflow', None)
        # A comment for all the frustrated developers which aren't able to pin
        # point the code which adds the review_state to the catalog. :)
        # The review_state var and some other workflow vars are added to the 
        # indexable object wrapper throught the code in the following lines
        if wf is not None:
            vars = wf.getCatalogVariablesFor(object)
        else:
            vars = {}
        portal = aq_parent(aq_inner(self))
        w = ExtensibleIndexableObjectWrapper(vars, object, portal=portal)
        try:
            ZCatalog.catalog_object(self, w, uid, idxs, update_metadata)
        except TypeError:
            ZCatalog.catalog_object(self, w, uid, idxs)


CatalogTool.__doc__ = BaseTool.__doc__

InitializeClass(CatalogTool)
