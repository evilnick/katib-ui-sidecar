#!/usr/bin/env python3
# Copyright 2021 evilnick
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus, WaitingStatus
from ops.pebble import Layer, ConnectionError
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class KatibUiCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.katib_ui_pebble_ready, self._pebble_ready)
        self.framework.observe(self.on.config_changed, self._apply_layer)
        # self.framework.observe(self.on.ingress_relation_changed, self.ingress_relation)
        self.ingress = IngressRequires(
                        self, {"service-hostname": "katib-ui",
                        "service-name": "katib-ui",
                        "service-port": self.config["port"]})
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
