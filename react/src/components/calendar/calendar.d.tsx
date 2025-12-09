import React from 'react';

export declare function setup(props: SetupProps): React.ReactElement;

export interface SetupProps {
  inputField?: string | undefined
  displayArea?: string | undefined
  button?: string | undefined
  eventName?: string
  ifFormat?: string
  daFormat?: string
  singleClick?: boolean | true
  disableFunc?: string
  dateStatusFunc?: string // takes precedence if both are defined
  mondayFirst?: boolean
  align?: string
  range?: []
  weekNumbers?: boolean
  flat?: boolean
  flatCallback?: string
  onSelect?: boolean
  onClose?: boolean
  onUpdate?: boolean
  date?: string
  showsTime?: boolean
  timeFormat?: string
  displayStatusBars?: boolean
}
