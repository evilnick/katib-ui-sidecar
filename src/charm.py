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
        self.framework.observe(self.on.katib_ui_pebble_ready, self._on_katib_ui_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # self.framework.observe(self.on.ingress_relation_changed, self.ingress_relation)
        self.ingress = IngressRequires(
                        self, {"service-hostname": "katib-ui",
                        "service-name": "katib-ui",
                        "service-port": self.config["port"]})
        self._stored.set_default(store={})

    def _on_katib_ui_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
        """
        # Get a reference to the container attribute on the PebbleReadyEvent
        container = self.unit.get_container("katib-ui")
        # Define an initial Pebble layer configuration
        pebble_layer = {
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
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("katib-ui", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        #TODO: katib-ui also needs a service account, check how to add this
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event):
        # Update port for katib from config 
        logger.debug("port reconfigured to : %r", self.config["port"])
        # N.B. currently, there is only a single config value. As this
        # event is not triggered unless the value *changes* (i.e. 
        # running juju config and setting the port to the same value
        # will not trigger this event), there is no need to check if 
        # the port has changed - it definitely has.
        self.unit.status = MaintenanceStatus("Configuring")
        # katib-ui needs to be re-run with the new port 
        try:
            container = self.unit.get_container("katib-ui")
            if container.get_service("katib-ui").is_running():
                container.stop("katib-ui")
                logger.info("container stopped for port change")
            
            container.start('katib-ui')
            # as the actual port config is supplied in the service command, restarting should be sufficient to change it        
            logger.info("Finished config_changed")
            self.unit.status = ActiveStatus()
        except ConnectionError:
            # there is no container
            self.unit.status = WaitingStatus("Waiting for Pebble")


if __name__ == "__main__":
    main(KatibUiCharm)
