#
# Tests the PloneTool
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFPlone.tests import dummy
from Products.CMFCore.utils import getToolByName

from Products.CMFPlone.browser.navtree import *

default_user = PloneTestCase.default_user

class TestFolderTree(PloneTestCase.PloneTestCase):
    '''Test the basic buildFolderTree method'''
    
    def afterSetUp(self):
        self.populateSite()

    def populateSite(self):
        """
            Portal
            +-doc1
            +-doc2
            +-doc3
            +-folder1
              +-doc11
              +-doc12
              +-doc13
            +-link1
            +-folder2
              +-doc21
              +-doc22
              +-doc23
              +-file21
              +-folder21
                +-doc211
                +-doc212
        """
        self.setRoles(['Manager'])
        
        for item in self.portal.getFolderContents():
            self.portal._delObject(item.getId)
        
        self.portal.invokeFactory('Document', 'doc1')
        self.portal.invokeFactory('Document', 'doc2')
        self.portal.invokeFactory('Document', 'doc3')
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Link', 'link1')
        self.portal.link1.setRemoteUrl('http://plone.org')
        self.portal.link1.reindexObject()
        folder1 = getattr(self.portal, 'folder1')
        folder1.invokeFactory('Document', 'doc11')
        folder1.invokeFactory('Document', 'doc12')
        folder1.invokeFactory('Document', 'doc13')
        self.portal.invokeFactory('Folder', 'folder2')
        folder2 = getattr(self.portal, 'folder2')
        folder2.invokeFactory('Document', 'doc21')
        folder2.invokeFactory('Document', 'doc22')
        folder2.invokeFactory('Document', 'doc23')
        folder2.invokeFactory('File', 'file21')
        folder2.invokeFactory('Folder', 'folder21')
        folder21 = getattr(folder2, 'folder21')
        folder21.invokeFactory('Document', 'doc211')
        folder21.invokeFactory('Document', 'doc212')
        self.setRoles(['Member'])

    # Get from the root, filters

    def testGetFromRoot(self):
        tree = buildFolderTree(self.portal)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 3)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[3]['children'][1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[3]['children'][2]['item'].getPath(), rootPath + '/folder1/doc13')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 5)
        self.assertEqual(tree[5]['children'][0]['item'].getPath(), rootPath + '/folder2/doc21')
        self.assertEqual(tree[5]['children'][1]['item'].getPath(), rootPath + '/folder2/doc22')
        self.assertEqual(tree[5]['children'][2]['item'].getPath(), rootPath + '/folder2/doc23')
        self.assertEqual(tree[5]['children'][3]['item'].getPath(), rootPath + '/folder2/file21')
        self.assertEqual(tree[5]['children'][4]['item'].getPath(), rootPath + '/folder2/folder21')
        self.assertEqual(len(tree[5]['children'][4]['children']), 2)
        self.assertEqual(tree[5]['children'][4]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21/doc211')
        self.assertEqual(tree[5]['children'][4]['children'][1]['item'].getPath(), rootPath + '/folder2/folder21/doc212')
        
    def testGetFromRootWithSpecifiedRoot(self):
        rootPath = '/'.join(self.portal.getPhysicalPath())
        strategy = NavtreeStrategyBase()
        strategy.rootPath = rootPath + '/folder1'
        tree = buildFolderTree(self.portal, strategy=strategy)['children']
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/folder1/doc13')
        
    def testGetFromRootWithNodeFilter(self):
        class Strategy(NavtreeStrategyBase):
            def nodeFilter(self, node):
                return ('doc' not in node['item'].getId)
        tree = buildFolderTree(self.portal, strategy=Strategy())['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[0]['children']), 0)
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[2]['children']), 2)
        self.assertEqual(tree[2]['children'][0]['item'].getPath(), rootPath + '/folder2/file21')
        self.assertEqual(tree[2]['children'][1]['item'].getPath(), rootPath + '/folder2/folder21')
        self.assertEqual(len(tree[2]['children'][1]['children']), 0)

    def testGetFromRootWithNodeFilterOnFolder(self):
        class Strategy(NavtreeStrategyBase):
            def nodeFilter(self, node):
                return ('folder' not in node['item'].getId)
        tree = buildFolderTree(self.portal, strategy=Strategy())['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 4)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/link1')

    def testGetFromRootWithSubtreeFilter(self):
        class Strategy(NavtreeStrategyBase):
            def subtreeFilter(self, node):
                return ('folder2' != node['item'].getId)
        tree = buildFolderTree(self.portal, strategy=Strategy())['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 3)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[3]['children'][1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[3]['children'][2]['item'].getPath(), rootPath + '/folder1/doc13')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 0)

    def testNonFolderishObjectNotExpanded(self):
        self.setRoles(['Manager'])
        f = dummy.FullNonStructuralFolder('ns_folder')
        self.portal._setObject('ns_folder', f)
        self.portal.ns_folder.reindexObject()
        self.portal.reindexObject()
        self.portal.ns_folder.invokeFactory('Document', 'doc')
        self.setRoles(['Member'])
        tree = buildFolderTree(self.portal, self.portal.ns_folder)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(tree[-1]['item'].getPath(), rootPath + '/ns_folder')
        self.assertEqual(len(tree[-1]['children']), 0)

    def testShowAllParentsOverridesNonFolderishObjectNotExpanded(self):
        strategy = NavtreeStrategyBase()
        strategy.showAllParents = True
        self.setRoles(['Manager'])
        f = dummy.FullNonStructuralFolder('ns_folder')
        self.portal._setObject('ns_folder', f)
        self.portal.ns_folder.reindexObject()
        self.portal.reindexObject()
        self.portal.ns_folder.invokeFactory('Document', 'doc')
        self.setRoles(['Member'])
        tree = buildFolderTree(self.portal, self.portal.ns_folder.doc, strategy=strategy)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(tree[-1]['item'].getPath(), rootPath + '/ns_folder')
        self.assertEqual(len(tree[-1]['children']), 1)
        self.assertEqual(tree[-1]['children'][0]['item'].getPath(), rootPath + '/ns_folder/doc')

    def testGetWithRootContext(self):
        tree = buildFolderTree(self.portal, context=self.portal)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 3)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[3]['children'][1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[3]['children'][2]['item'].getPath(), rootPath + '/folder1/doc13')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 5)
        self.assertEqual(tree[5]['children'][0]['item'].getPath(), rootPath + '/folder2/doc21')
        self.assertEqual(tree[5]['children'][1]['item'].getPath(), rootPath + '/folder2/doc22')
        self.assertEqual(tree[5]['children'][2]['item'].getPath(), rootPath + '/folder2/doc23')
        self.assertEqual(tree[5]['children'][3]['item'].getPath(), rootPath + '/folder2/file21')
        self.assertEqual(tree[5]['children'][4]['item'].getPath(), rootPath + '/folder2/folder21')
        self.assertEqual(len(tree[5]['children'][4]['children']), 2)
        self.assertEqual(tree[5]['children'][4]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21/doc211')
        self.assertEqual(tree[5]['children'][4]['children'][1]['item'].getPath(), rootPath + '/folder2/folder21/doc212')

    def testGetFromFixed(self):
        rootPath = '/'.join(self.portal.getPhysicalPath())
        query = {'path' : rootPath + '/folder1'}
        tree = buildFolderTree(self.portal, query=query)['children']
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/folder1/doc13')

    def testGetFromFixedAndDepth(self):
        rootPath = '/'.join(self.portal.getPhysicalPath())
        query = {'path' : rootPath + '/folder2', 'depth' : 1}
        tree = buildFolderTree(self.portal, query=query)['children']
        self.assertEqual(len(tree), 5)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder2/doc21')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder2/doc22')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/folder2/doc23')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder2/file21')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/folder2/folder21')

    def testGetFromRootWithCurrent(self):
        context = self.portal.folder2.doc21
        tree = buildFolderTree(self.portal, context=context)['children']
        self.assertEqual(len(tree), 6)
        for t in tree:
            if t['item'].getId == 'folder2':
                self.assertEqual(t['currentItem'], False)
                self.assertEqual(t['currentParent'], True)
                for c in t['children']:
                    if c['item'].getId == 'doc21':
                        self.assertEqual(c['currentItem'], True)
                        self.assertEqual(c['currentParent'], False)
                    else:
                        self.assertEqual(c['currentItem'], False)
                        self.assertEqual(c['currentParent'], False)
            else:
                self.assertEqual(t['currentItem'], False)
                self.assertEqual(t['currentParent'], False)

    def testGetFromRootIgnoresDefaultPages(self):
        self.portal.folder1.setDefaultPage('doc12')
        self.portal.folder2.setDefaultPage('doc21')
        tree = buildFolderTree(self.portal)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 2)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[3]['children'][1]['item'].getPath(), rootPath + '/folder1/doc13')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 4)
        self.assertEqual(tree[5]['children'][0]['item'].getPath(), rootPath + '/folder2/doc22')
        self.assertEqual(tree[5]['children'][1]['item'].getPath(), rootPath + '/folder2/doc23')
        self.assertEqual(tree[5]['children'][2]['item'].getPath(), rootPath + '/folder2/file21')
        self.assertEqual(tree[5]['children'][3]['item'].getPath(), rootPath + '/folder2/folder21')
        self.assertEqual(len(tree[5]['children'][3]['children']), 2)
        self.assertEqual(tree[5]['children'][3]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21/doc211')
        self.assertEqual(tree[5]['children'][3]['children'][1]['item'].getPath(), rootPath + '/folder2/folder21/doc212')
                
    def testGetFromRootWithCurrentIsDefaultPage(self):
        self.portal.folder2.setDefaultPage('doc21')
        context = self.portal.folder2.doc21
        tree = buildFolderTree(self.portal, context=context)['children']
        for t in tree:
            if t['item'].getId == 'folder2':
                self.assertEqual(t['currentItem'], True)
                self.assertEqual(t['currentParent'], False)
                for c in t['children']:
                    self.assertEqual(c['currentItem'], False)
                    self.assertEqual(c['currentParent'], False)
            else:
                self.assertEqual(t['currentItem'], False)
                self.assertEqual(t['currentParent'], False)

    def testGetFromRootWithCustomQuery(self):
        query = {'portal_type' : 'Document'}
        tree = buildFolderTree(self.portal, query=query)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')

    def testGetFromRootWithDecoratorFactory(self):
        class Strategy(NavtreeStrategyBase):
            def decoratorFactory(self, node):
                node['foo'] = True
                return node
        tree = buildFolderTree(self.portal, strategy=Strategy())['children']
        self.assertEqual(tree[0]['foo'], True)

    def testShowAllParents(self):
        strategy = NavtreeStrategyBase()
        strategy.showAllParents = True
        query = {'portal_type' : 'Folder'}
        context = self.portal.folder1.doc11
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=strategy)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[1]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21')

    def testShowAllParentsWithRestrictedParent(self):
        strategy = NavtreeStrategyBase()
        strategy.showAllParents = True
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.doActionFor(self.portal.folder1, 'hide')
        self.portal.folder1.reindexObject()
        query = {'portal_type' : 'Folder'}
        context = self.portal.folder1.doc11
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=strategy)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[1]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21')

    def testShowAllParentsWithParentNotInCatalog(self):
        strategy = NavtreeStrategyBase()
        strategy.showAllParents = True
        wftool = getToolByName(self.portal, 'portal_workflow')
        self.portal.folder1.unindexObject()
        query = {'portal_type' : 'Folder'}
        context = self.portal.folder1.doc11
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=strategy)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        # XXX: Ideally, this shouldn't happen, we should get a dummy node, but
        # there's no way to do that with the catalog
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder2')

    def testDontShowAllParents(self):
        strategy = NavtreeStrategyBase()
        strategy.showAllParents = False
        query = {'portal_type' : 'Folder'}
        context = self.portal.folder1.doc11
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=strategy)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[0]['children']), 0)
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[1]['children']), 1)
        self.assertEqual(tree[1]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21')

    def testGetFromRootWithCurrentNavtree(self):
        context = self.portal.folder1.doc11
        query = {'path' : {'query' : '/'.join(context.getPhysicalPath()),
                           'navtree' : 1}}
        tree = buildFolderTree(self.portal, query=query)['children']
        rootPath = '/'.join(self.portal.getPhysicalPath())
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 3)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[3]['children'][1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[3]['children'][2]['item'].getPath(), rootPath + '/folder1/doc13')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 0)

    def testGetFromRootWithCurrentNavtreeAndStartLevel(self):
        context = self.portal.folder1.doc11
        query = {'path' : {'query' : '/'.join(context.getPhysicalPath()),
                           'navtree' : 1,
                           'navtree_start' : 2}}
        rootPath = '/'.join(self.portal.getPhysicalPath())
        tree = buildFolderTree(self.portal, query=query)['children']
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/folder1/doc12')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/folder1/doc13')
        
    def testGetFromRootWithCurrentNavtreePruned(self):
        context = self.portal.folder1.doc11
        class Strategy(NavtreeStrategyBase):
            def subtreeFilter(self, node):
                return (node['item'].getId != 'folder1')
            showAllParents = True
            
        query = {'path' : {'query' : '/'.join(context.getPhysicalPath()),
                           'navtree' : 1}}
        rootPath = '/'.join(self.portal.getPhysicalPath())
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=Strategy())['children']
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 1)
        self.assertEqual(tree[3]['children'][0]['item'].getPath(), rootPath + '/folder1/doc11')
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 0)
        
    def testGetFromRootWithCurrentFolderishNavtreePruned(self):
        context = self.portal.folder2.folder21
        class Strategy(NavtreeStrategyBase):
            def subtreeFilter(self, node):
                return (node['item'].getId != 'folder2')
            showAllParents=True
            
        query = {'path' : {'query' : '/'.join(context.getPhysicalPath()),
                           'navtree' : 1}}
        rootPath = '/'.join(self.portal.getPhysicalPath())
        tree = buildFolderTree(self.portal, query=query, context=context, strategy=Strategy())['children']
        self.assertEqual(len(tree), 6)
        self.assertEqual(tree[0]['item'].getPath(), rootPath + '/doc1')
        self.assertEqual(tree[1]['item'].getPath(), rootPath + '/doc2')
        self.assertEqual(tree[2]['item'].getPath(), rootPath + '/doc3')
        self.assertEqual(tree[3]['item'].getPath(), rootPath + '/folder1')
        self.assertEqual(len(tree[3]['children']), 0)
        self.assertEqual(tree[4]['item'].getPath(), rootPath + '/link1')
        self.assertEqual(tree[5]['item'].getPath(), rootPath + '/folder2')
        self.assertEqual(len(tree[5]['children']), 1)
        self.assertEqual(tree[5]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21')
        self.assertEqual(len(tree[5]['children'][0]['children']), 2)
        self.assertEqual(tree[5]['children'][0]['children'][0]['item'].getPath(), rootPath + '/folder2/folder21/doc211')
        self.assertEqual(tree[5]['children'][0]['children'][1]['item'].getPath(), rootPath + '/folder2/folder21/doc212')

class TestNavigationRoot(PloneTestCase.PloneTestCase):
    
    def testGetNavigationRootPropertyNotSet(self):
        self.portal.portal_properties.navtree_properties._delProperty('root')
        root = getNavigationRoot(self.portal, self.portal)
        self.assertEqual(root, '/'.join(self.portal.getPhysicalPath()))
        
    def testGetNavigationRootPropertyEmptyNoVirtualHost(self):
        self.portal.portal_properties.navtree_properties.manage_changeProperties(root='')
        root = getNavigationRoot(self.portal, self.portal)
        self.assertEqual(root, '/'.join(self.portal.getPhysicalPath()))

    # XXX: If we re-enable this in PloneTool, we should fix up this test
    # def testGetNavigationRootPropertyEmptyWithVirtualHost(self):
    #    self.fail('Test missing (see Sprout, which this code was stolen from)')

    def testGetNavigationRootPropertyIsRoot(self):
        self.portal.portal_properties.navtree_properties.manage_changeProperties(root='/')
        root = getNavigationRoot(self.portal, self.portal)
        self.assertEqual(root, '/'.join(self.portal.getPhysicalPath()))

    def testGetNavigationRootPropertyIsFolder(self):
        folderPath = '/'.join(self.folder.getPhysicalPath())
        portalPath = '/'.join(self.portal.getPhysicalPath())
        relativePath = folderPath[len(portalPath):]
        self.portal.portal_properties.navtree_properties.manage_changeProperties(root=relativePath)
        root = getNavigationRoot(self.portal, self.portal)
        self.assertEqual(root, folderPath)

    def testGetNavigationRootPropertyIsCurrentFolderish(self):
        folderPath = '/'.join(self.folder.getPhysicalPath())
        self.portal.portal_properties.navtree_properties.manage_changeProperties(root='.')
        root = getNavigationRoot(self.portal, self.folder)
        self.assertEqual(root, folderPath)

    def testGetNavigationRootPropertyIsCurrentNonFolderish(self):
        self.folder.invokeFactory('Document', 'foo')
        folderPath = '/'.join(self.folder.getPhysicalPath())
        self.portal.portal_properties.navtree_properties.manage_changeProperties(root='.')
        root = getNavigationRoot(self.portal, self.folder.foo)
        self.assertEqual(root, folderPath)
        
    def testGetNavigationRootWithTopLevel(self):
        self.folder.invokeFactory('Document', 'foo')
        folderPath = '/'.join(self.folder.getPhysicalPath())
        self.portal.portal_properties.navtree_properties.manage_changeProperties(topLevel=2)
        root = getNavigationRoot(self.portal, self.folder.foo, topLevel=2)
        self.assertEqual(root, folderPath)

    def testGetNavigationRootWithTopLevelAndEmptyRoot(self):
        self.folder.invokeFactory('Document', 'foo')
        folderPath = '/'.join(self.folder.getPhysicalPath())
        self.portal.portal_properties.navtree_properties.manage_changeProperties(topLevel=2, root='')
        root = getNavigationRoot(self.portal, self.folder.foo, topLevel=2)
        self.assertEqual(root, folderPath)

    def testGetNavigationRootWithTopLevelAndRoot(self):
        folderPath = '/'.join(self.folder.getPhysicalPath())
        portalPath = '/'.join(self.portal.getPhysicalPath())
        relativePath = folderPath[len(portalPath):]
        self.folder.invokeFactory('Folder', 'foo')
        self.folder.foo.invokeFactory('Document', 'bar')
        folderPath = '/'.join(self.folder.getPhysicalPath())
        self.portal.portal_properties.navtree_properties.manage_changeProperties(topLevel=1, root=relativePath)
        root = getNavigationRoot(self.portal, self.folder.foo.bar, topLevel=1)
        self.assertEqual(root, folderPath + '/foo')
    
    def testGetNavigationRootWithTopLevelAndContextOutsideRoot(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Folder', 'foo')
        self.setRoles(['Member'])
        self.portal.portal_properties.navtree_properties.manage_changeProperties(topLevel=1, root='/foo')
        root = getNavigationRoot(self.portal, self.folder, topLevel=1)
        self.assertEqual(root, None)

# XXX: This tests the navtree using the 2.1 compatability decorator and methods.
# It would be preferable to check node['item'] instead of properties injected
# in the node, but we can't break any customisations of the navtree portlet
# or other code depending on this method in the middle of a release cycle.
class TestNavTree(PloneTestCase.PloneTestCase):
    '''Tests for the new navigation tree and sitemap'''

    def afterSetUp(self):
        self.utils = self.portal.plone_utils
        self.populateSite()

    def populateSite(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'doc1')
        self.portal.invokeFactory('Document', 'doc2')
        self.portal.invokeFactory('Document', 'doc3')
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Link', 'link1')
        self.portal.link1.setRemoteUrl('http://plone.org')
        self.portal.link1.reindexObject()
        folder1 = getattr(self.portal, 'folder1')
        folder1.invokeFactory('Document', 'doc11')
        folder1.invokeFactory('Document', 'doc12')
        folder1.invokeFactory('Document', 'doc13')
        self.portal.invokeFactory('Folder', 'folder2')
        folder2 = getattr(self.portal, 'folder2')
        folder2.invokeFactory('Document', 'doc21')
        folder2.invokeFactory('Document', 'doc22')
        folder2.invokeFactory('Document', 'doc23')
        folder2.invokeFactory('File', 'file21')
        self.setRoles(['Member'])

    def testTypesToList(self):
        # Make sure typesToList() returns the expected types
        wl = self.utils.typesToList()
        self.failUnless('Folder' in wl)
        self.failUnless('Large Plone Folder' in wl)
        self.failUnless('Topic' in wl)
        self.failIf('ATReferenceCriterion' in wl)

    def testCreateNavTree(self):
        # See if we can create one at all
        tree = self.utils.createNavTree(self.portal)
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))

    def testCreateNavTreeCurrentItem(self):
        # With the context set to folder2 it should return a dict with
        # currentItem set to True
        tree = self.utils.createNavTree(self.portal.folder2)
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['currentItem'], True)

    def testCreateNavTreeRespectsTypesWithViewAction(self):
        # With a File or Image as current action it should return a
        # currentItem which has '/view' appended to the url
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        # Fail if 'view' is used for parent folder; it should only be on the File
        self.failIf(tree['children'][-1]['absolute_url'][-5:]=='/view')
        # Verify we have the correct object and it is the current item
        self.assertEqual(tree['children'][-1]['children'][-1]['currentItem'],True)
        self.assertEqual(tree['children'][-1]['children'][-1]['path'].split('/')[-1],'file21')
        # Verify that we have '/view'
        self.assertEqual(tree['children'][-1]['children'][-1]['absolute_url'][-5:],'/view')

    def testNavTreeExcludesItemsWithExcludeProperty(self):
        # Make sure that items witht he exclude_from_nav property set get
        # no_display set to True
        self.portal.folder2.setExcludeFromNav(True)
        self.portal.folder2.reindexObject()
        tree = self.utils.createNavTree(self.portal.folder1.doc11)
        self.failUnless(tree)
        for c in tree['children']:
            if c['path'] == '/portal/folder2':
                self.fail()

    def testShowAllParentsOverridesNavTreeExcludesItemsWithExcludeProperty(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        self.portal.folder2.setExcludeFromNav(True)
        self.portal.folder2.reindexObject()
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(showAllParents=True)
        tree = self.utils.createNavTree(self.portal.folder2.doc21)
        self.failUnless(tree)
        found = False
        for c in tree['children']:
            if c['path'] == '/portal/folder2':
                found = True
                break
        self.failUnless(found)

    def testNavTreeExcludesItemsInIdsNotToList(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(idsNotToList=['folder2'])
        tree = self.utils.createNavTree(self.portal.folder1.doc11)
        self.failUnless(tree)
        for c in tree['children']:
            if c['path'] == '/portal/folder2':
                self.fail()

    def testShowAllParentsOverridesNavTreeExcludesItemsInIdsNotToList(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(idsNotToList=['folder2'], showAllParents=True)
        tree = self.utils.createNavTree(self.portal.folder2.doc21)
        self.failUnless(tree)
        found = False
        for c in tree['children']:
            if c['path'] == '/portal/folder2':
                found = True
                break
        self.failUnless(found)

    def testNavTreeExcludesDefaultPage(self):
        # Make sure that items which are the default page are excluded
        self.portal.folder2.setDefaultPage('doc21')
        tree = self.utils.createNavTree(self.portal.folder1.doc11)
        self.failUnless(tree)
        # Ensure that our 'doc21' default page is not in the tree.
        self.assertEqual([c for c in tree['children'][-1]['children']
                                            if c['path'][-5:]=='doc21'],[])

    def testNavTreeMarksParentMetaTypesNotToQuery(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property get no_display set to True
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.assertEqual(tree['children'][-1]['show_children'],True)
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(parentMetaTypesNotToQuery=['Folder'])
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.assertEqual(tree['children'][-1]['show_children'],False)

    def testCreateNavTreeWithLink(self):
        tree = self.utils.createNavTree(self.portal)
        for child in tree['children']:
            if child['portal_type'] != 'Link':
                self.failIf(child['getRemoteUrl'])
            if child['Title'] == 'link1':
                self.failUnlessEqual(child['getRemoteUrl'], 'http://plone.org')

    def testNonStructuralFolderHidesChildren(self):
        # Make sure NonStructuralFolders act as if parentMetaTypesNotToQuery
        # is set.
        f = dummy.NonStructuralFolder('ns_folder')
        self.folder._setObject('ns_folder', f)
        self.portal.portal_catalog.reindexObject(self.folder.ns_folder)
        self.portal.portal_catalog.reindexObject(self.folder)
        tree = self.utils.createNavTree(self.folder.ns_folder)
        self.assertEqual(tree['children'][0]['children'][0]['children'][0]['path'],
                                '/portal/Members/test_user_1_/ns_folder')
        self.assertEqual(tree['children'][0]['children'][0]['children'][0]['show_children'],False)

    def testTopLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['path'], '/portal/folder2/file21')

    def testTopLevelWithContextAboveLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        tree = self.utils.createNavTree(self.portal)
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 0)

    def testTopLevelTooDeep(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=5)
        tree = self.utils.createNavTree(self.portal)
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 0)

    def testTopLevelWithNavigationRoot(self):
        self.portal.folder2.invokeFactory('Folder', 'folder21')
        self.portal.folder2.folder21.invokeFactory('Document', 'doc211')
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1, root='/folder2')
        tree = self.utils.createNavTree(self.portal.folder2.folder21)
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 1)
        self.assertEqual(tree['children'][0]['path'], '/portal/folder2/folder21/doc211')

    def testTopLevelWithPortalFactory(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        id=self.portal.generateUniqueId('Document')
        typeName='Document'
        newObject=self.portal.folder1.restrictedTraverse('portal_factory/' + typeName + '/' + id)
        # Will raise a KeyError unless bug is fixed
        tree=self.utils.createNavTree(newObject)
    
    def testShowAllParentsOverridesBottomLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        # Note: showAllParents makes sure we actually return items on the,
        # path to the context, but the portlet will not display anything
        # below bottomLevel. 
        self.assertEqual(tree['children'][-1]['path'], '/portal/folder2')
        self.assertEqual(len(tree['children'][-1]['children']), 1)
        self.assertEqual(tree['children'][-1]['children'][0]['item'].getPath(), '/portal/folder2/file21')
        
    def testBottomLevelStopsAtFolder(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        tree = self.utils.createNavTree(self.portal.folder2)
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['path'], '/portal/folder2')
        self.assertEqual(len(tree['children'][-1]['children']), 0)
        
    def testNoRootSet(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='')
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['path'], '/portal/folder2')
        
    def testRootIsPortal(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/')
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['path'], '/portal/folder2')
        
    def testRootIsNotPortal(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/folder2')
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['path'], '/portal/folder2/doc21')

    def testRootDoesNotExist(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/dodo')
        tree = self.utils.createNavTree(self.portal.folder2.file21)
        self.failUnless(tree)
        self.assertEqual(tree.get('item', None), None)
        self.assertEqual(len(tree['children']), 0)

    def testRootIsCurrent(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='.')
        tree = self.utils.createNavTree(self.portal.folder2)
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['path'], '/portal/folder2/doc21')

    def testCreateSitemap(self):
        # Internally createSitemap is the same as createNavTree
        tree = self.utils.createSitemap(self.portal)
        self.failUnless(tree)

    def testCustomQuery(self):
        # Try a custom query script for the navtree that returns only published
        # objects
        workflow = self.portal.portal_workflow
        factory = self.portal.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript('getCustomNavQuery')
        script = self.portal.getCustomNavQuery
        script.ZPythonScript_edit('','return {"review_state":"published"}')
        self.assertEqual(self.portal.getCustomNavQuery(),{"review_state":"published"})
        tree = self.utils.createNavTree(self.portal.folder2)
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))
        #Should only contain current object
        self.assertEqual(len(tree['children']), 1)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        tree = self.utils.createNavTree(self.portal.folder2)
        #Should only contain current object and published folder
        self.assertEqual(len(tree['children']), 2)

    def testStateFiltering(self):
        # Test Navtree workflow state filtering
        workflow = self.portal.portal_workflow
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(wf_states_to_show=['published'])
        ntp.manage_changeProperties(enable_wf_state_filtering=True)
        tree = self.utils.createNavTree(self.portal.folder2)
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))
        #Should only contain current object
        self.assertEqual(len(tree['children']), 1)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        tree = self.utils.createNavTree(self.portal.folder2)
        #Should only contain current object and published folder
        self.assertEqual(len(tree['children']), 2)

    def testComplexSitemap(self):
        # create and test a reasonabley complex sitemap
        path = lambda x: '/'.join(x.getPhysicalPath())
        # We do this in a strange order in order to maximally demonstrate the bug
        folder1 = self.portal.folder1
        folder1.invokeFactory('Folder','subfolder1')
        subfolder1 = folder1.subfolder1
        folder1.invokeFactory('Folder','subfolder2')
        subfolder2 = folder1.subfolder2
        subfolder1.invokeFactory('Folder','subfolder11')
        subfolder11 = subfolder1.subfolder11
        subfolder1.invokeFactory('Folder','subfolder12')
        subfolder12 = subfolder1.subfolder12
        subfolder2.invokeFactory('Folder','subfolder21')
        subfolder21 = subfolder2.subfolder21
        folder1.invokeFactory('Folder','subfolder3')
        subfolder3 = folder1.subfolder3
        subfolder2.invokeFactory('Folder','subfolder22')
        subfolder22 = subfolder2.subfolder22
        subfolder22.invokeFactory('Folder','subfolder221')
        subfolder221 = subfolder22.subfolder221

        # Increase depth
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(sitemapDepth=5)

        sitemap = self.utils.createSitemap(self.portal)

        folder1map = sitemap['children'][6]
        self.assertEqual(len(folder1map['children']), 6)
        self.assertEqual(folder1map['path'], path(folder1))

        subfolder1map = folder1map['children'][3]
        self.assertEqual(subfolder1map['path'], path(subfolder1))
        self.assertEqual(len(subfolder1map['children']), 2)

        subfolder2map = folder1map['children'][4]
        self.assertEqual(subfolder2map['path'], path(subfolder2))
        self.assertEqual(len(subfolder2map['children']), 2)

        subfolder3map = folder1map['children'][5]
        self.assertEqual(subfolder3map['path'], path(subfolder3))
        self.assertEqual(len(subfolder3map['children']), 0)

        subfolder11map = subfolder1map['children'][0]
        self.assertEqual(subfolder11map['path'], path(subfolder11))
        self.assertEqual(len(subfolder11map['children']), 0)

        subfolder21map = subfolder2map['children'][0]
        self.assertEqual(subfolder21map['path'], path(subfolder21))
        self.assertEqual(len(subfolder21map['children']), 0)

        subfolder22map = subfolder2map['children'][1]
        self.assertEqual(subfolder22map['path'], path(subfolder22))
        self.assertEqual(len(subfolder22map['children']), 1)

        # Why isn't this showing up in the sitemap
        subfolder221map = subfolder22map['children'][0]
        self.assertEqual(subfolder221map['path'], path(subfolder221))
        self.assertEqual(len(subfolder221map['children']), 0)

    def testSitemapWithTopLevel(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        sitemap = self.utils.createSitemap(self.portal)
        self.assertEqual(sitemap['children'][-1]['path'], '/portal/folder2')
        
    def testSitemapWithBottomLevel(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        sitemap = self.utils.createSitemap(self.portal)
        self.assertEqual(sitemap['children'][-1]['path'], '/portal/folder2')
        self.failUnless(len(sitemap['children'][-1]['children']) > 0)
        
    def testSitemapWithNavigationRoot(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root = '/folder2')
        sitemap = self.utils.createSitemap(self.portal)
        self.assertEqual(sitemap['children'][-1]['path'], '/portal/folder2/file21')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFolderTree))
    suite.addTest(makeSuite(TestNavigationRoot))
    suite.addTest(makeSuite(TestNavTree))
    return suite

if __name__ == '__main__':
    framework()