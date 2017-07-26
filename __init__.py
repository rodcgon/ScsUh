# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ScsUh
                                 A QGIS plugin
 Generates SCS runoff UH from basin and rain data.
                             -------------------
        begin                : 2017-02-14
        copyright            : (C) 2017 by Rodrigo Goncalves
        email                : rodcgon@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ScsUh class from file ScsUh.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .SCSUH import ScsUh
    return ScsUh(iface)
