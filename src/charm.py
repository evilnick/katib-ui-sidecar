#!/usr/bin/env python3
# Copyright 2021 evilnick
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Sidecar charm for the katib-ui service."""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus, WaitingStatus
from ops.pebble import Layer, ConnectionError
from oci_image import OCIImageResource, OCIImageResourceError
from serialized_data_interface import NoCompatibleVersions, NoVersionsListed, get_interfaces

logger = logging.getLogger(__name__)


class KatibUiCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        
        try:
            self.interfaces = get_interfaces(self)
        except NoVersionsListed as err:
            self.model.unit.status = WaitingStatus(str(err))
            return
        except NoCompatibleVersions as err:
            self.model.unit.status = BlockedStatus(str(err))
            return
        else:
            self.model.unit.status = ActiveStatus()
        
        self.framework.observe(self.on.katib_ui_pebble_ready, self._pebble_ready)
        self.framework.observe(self.on.config_changed, self._apply_layer)
        self.framework.observe(self.on["ingress"].relation_changed, self._configure_ingress)
        self._stored.set_default(store={})


    def _pebble_ready(self, _):
        
        self._apply_layer( _)
        # katib-ui also needs a service account
        # TODO: add code for that here

    def _apply_layer(self, _):
        """Manage the container using the Pebble API."""
        try:
            self.unit.status = MaintenanceStatus("applying config")
            container = self.unit.get_container("katib-ui")
            container.add_layer("katib-ui", self.layer, combine=True)
            if container.get_service("katib-ui").is_running():
                container.stop("katib-ui")
            container.start("katib-ui")
            self.unit.status = ActiveStatus()
        except ConnectionError:
            self.unit.status = WaitingStatus("Waiting for Pebble")

    def _configure_ingress(self, event):
        """sends data for ingress relation"""
        if self.interfaces["ingress"]:
            self.interfaces["ingress"].send_data(
                {
                    "prefix": "/katib/",
                    "service": self.model.app.name,
                    "port": self.model.config["port"],
                }
            )

    @property
    def layer(self):
        """Pebble layer"""
        return Layer(
            {
            "summary": "katib-ui layer",
            "description": "pebble config layer for katib-ui",
            "services": {
                "katib-ui": {
                    "override": "replace",
                    "summary": "katib-ui",
                    "command": f"./katib-ui --port={self.model.config['port']}",
                    "startup": "enabled",
                    "environment": {"KUBERNETES_POD_NAMESPACE": self.model.name},
                }
            }
        }
    )        

if __name__ == "__main__":
    main(KatibUiCharm)
