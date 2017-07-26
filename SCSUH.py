# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ScsUh
                                 A QGIS plugin
 Generates SCS runoff UH from basin and rain data.
                              -------------------
        begin                : 2017-02-14
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Rodrigo Goncalves
        email                : rodcgon@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt4.QtGui import QAction, QIcon,QTableWidgetItem, QFileDialog
from qgis.core import QgsMapLayer, QgsField, QgsProject
# Initialize Qt resources from file resources.py
import resources, datetime, csv
# Import the code for the dialog
from SCSUH_dialog import ScsUhDialog
import os.path
from functools import partial
from scs_v5_qgis import *


class ScsUh:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ScsUh_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SCS Unit Hydrograph')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ScsUh')
        self.toolbar.setObjectName(u'ScsUh')

        # Create the dialog (after translation) and keep reference
        self.dlg = ScsUhDialog()

        # os 'connect' sempre vem aqui no init, pra nao ficar repetindo ligacao
        self.completaIDF()
        self.dlg.pbCalc.clicked.connect(self.leCampos)
        self.dlg.pbPath.clicked.connect(self.saveB)
        self.dlg.cbSWMM.stateChanged.connect(self.camposSWMM)
        self.dlg.cbRes.stateChanged.connect(partial(self.campoDir,'cbRes'))
        self.dlg.cbHid.stateChanged.connect(partial(self.campoDir,'cbHid'))

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ScsUh', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """



        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ScsUh/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SCS UH'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SCS Unit Hydrograph'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def encheCombo(self,cb, dic0):
        cb.clear()
        cb.addItems(dic0.keys())

    def leTabela(self, tabela):
        lins, cols = tabela.rowCount(), tabela.columnCount()
        data =[]
        for l in range(lins):
            linha = []
            for c in range(cols):
                linha.append(tabela.item(l,c).text())
            data.append(linha)
        return data

    def escSWMM(self,aTab,pathC,DT):
        dIni = str(self.dlg.leHoraIni.text())
        dtI = datetime.datetime.strptime(dIni,'%d/%m/%Y %H:%M')
        hrI = dtI.strftime('%H:M')
        lstQ = np.round(aTab[:,4],decimals=3).tolist()
        numReg = len(lstQ)
        lstH = [dtI + datetime.timedelta(minutes=DT*x) for x in range(0, numReg)]
        data = [d.strftime('%H:%M') for d in lstH]
        #data = ["%02d:%02d" % (int(h),(h-int(h))*60) for h in aTab[:,0].tolist()]
        #data = [datetime.datetime.strptime(str(d),'%H').strftime('%H:%M') for d in aTab[:,0].tolist()]
        lstQ = np.round(aTab[:,4],decimals=3).tolist()
        lstD = [dtI.strftime('%m/%d/%Y')]+(len(lstQ)-1)*['     ']
        lstF = map(list, zip(lstD,data,lstQ))
        with open(pathC,'wb') as fn:
            wr = csv.writer(fn,delimiter=' ', quoting=csv.QUOTE_NONE, quotechar='',escapechar=' ')
            wr.writerows(lstF)

    def leCampos(self):
        dicL = {l.name(): l for l in self.iface.mapCanvas().layers() if l.type()==QgsMapLayer.VectorLayer}
        lV = dicL[str(self.dlg.cbPointLayer.currentText())]
        print lV, lV.name()
        nomes = [f.name() for f in lV.pendingFields()]
        iA, iTC, iCN, iImp,iNome = 0,0,0,0,0
        for n in nomes:
            if 'area' in n.lower():
                iA = nomes.index(n)
            if 'tc' in n.lower():
                iTC = nomes.index(n)
            if 'cn' in n.lower():
                iCN = nomes.index(n)
            if 'imp' in n.lower():
                iImp = nomes.index(n)
            if 'nome' in n.lower():
                iNome = nomes.index(n)
        lstC = []   #list of attributes of the feature 
        if self.dlg.cbSel.isChecked():
            features = lV.selectedFeatures()
        else:
            features = lV.getFeatures()
        for feat in features:
            attrs = feat.attributes()
            if float(attrs[1])>0:   # acho que foi pra se a área foi maior que zero
                lstC.append(attrs)
        
        dicIdQ={}
        for c in lstC:
            A,TC,CNIni,Imp = c[iA],c[iTC],c[iCN],c[iImp]
            nomeB = c[iNome]
            idf = [float(d) for d in self.leTabela(self.dlg.twIDF)[0]]
            DUR = float(self.dlg.leDur.text())
            DT = float(self.dlg.leDT.text())
            TR = float(self.dlg.leTR.text())
            #print c
            #print A,TC,TR,DUR,DT,CNIni,Imp,idf
            aTab,blalt,aLoss,aHidroF,DT,aVolm3 = geraHidro(A,TC,TR,DUR,DT,CNIni,Imp,idf)
            data1 = datetime.datetime.now().strftime('%d-%m-%Y_%H%M%S')
            if self.dlg.cbSWMM.isChecked():
                path1 = str(self.dlg.lePath.text())
                fname1= nomeB +'_A'+str(A)+'TR'+str(TR)+'_'+data1+'.dat'
                self.escSWMM(aTab,path1+os.sep+fname1,DT)
            if self.dlg.cbRes.isChecked():
                path1 = str(self.dlg.lePath.text())
                lstPCSV = [A,CNIni,Imp,TC,TR,idf,DUR,DT,aTab]
                nomeRes = path1+os.sep+'tab_'+nomeB+'_A'+str(A)+'TR'+str(TR)+'_'+data1+'.csv'
                escreveCSV(nomeRes, lstPCSV)
            if self.dlg.cbHid.isChecked():
                path1 = str(self.dlg.lePath.text())
                nomePlot = path1+os.sep+'hidro_'+nomeB+'_TR'+str(int(TR))+'_'+data1+'.pdf'
                geraPlot(nomePlot,blalt,aLoss,aHidroF,DT,aVolm3)
            qmax = np.max(aTab[:,4])
            dicIdQ[c[iNome]]=float(qmax)
        if ("Q "+str(TR)+ "m3/s") not in lV.pendingFields()[-1].name():
            lV.startEditing()
            lV.dataProvider().addAttributes([QgsField("Q "+str(TR)+ "m3/s", QVariant.Double, "double", 15,2)])
            lV.commitChanges()
        ultAtt = lV.pendingFields().allAttributesList()[-1]

        if self.dlg.cbSel.isChecked():
            features = lV.selectedFeatures()
        else:
            features = lV.getFeatures()
        lV.startEditing()
        for fet in features:
            fid = int(fet.id())
            primAt = lV.pendingFields().allAttributesList()[0]
            fet[ultAtt]=dicIdQ[fet[iNome]]
            lV.updateFeature(fet)
        lV.commitChanges()

    def completaIDF(self):
        lIDF=[[0,0,0,0],[1133.836,.183,20.667,0.807],[1239.0,0.150,20.00,0.740],[3281.158,.222,44.204,1.0]]
        #n = int(self.dlg.cbIDF.currentIndex())
        j=0
        for it in lIDF[3]:
            self.dlg.twIDF.setItem(0, j, QTableWidgetItem(str(it)))
            j+=1

    def saveB(self):
        #str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        fileN =str(QFileDialog.getExistingDirectory(self.dlg, u"Selecione diretório:",QgsProject.instance().readPath("./")))
        self.dlg.lePath.setText(fileN)

    def camposSWMM(self):
        if self.dlg.cbSWMM.isChecked():
            self.dlg.leHoraIni.setEnabled(True)
            self.dlg.lePath.setEnabled(True)
            self.dlg.pbPath.setEnabled(True)
        else:
            self.dlg.leHoraIni.setEnabled(False)
            self.dlg.lePath.setEnabled(False)
            self.dlg.pbPath.setEnabled(False)

    def campoDir(self,campo):
        c1 = eval('self.dlg.'+campo)
        if c1.isChecked():
            self.dlg.lePath.setEnabled(True)
            self.dlg.pbPath.setEnabled(True)
        else:
            self.dlg.lePath.setEnabled(False)
            self.dlg.pbPath.setEnabled(False)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        dicPL = {l.name(): l for l in self.iface.mapCanvas().layers() if l.type()==QgsMapLayer.VectorLayer}
        print dicPL
        #and l.wkbType()==1 #point
        self.encheCombo(self.dlg.cbPointLayer,dicPL)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
